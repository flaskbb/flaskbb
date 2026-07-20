# -*- coding: utf-8 -*-
"""
flaskbb.core.search.tantivy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A search backend built on Tantivy (a Rust full-text search engine).
Each searchable model gets its own on-disk Tantivy index (under `SEARCH_INDEX_DIR`),
keyed on the model's primary key plus a single combined, tokenized text field.

The index is kept in sync via via SQLAlchemy session events `after_flush`,
`after_commit` and `after_rollback`.

However, only ORM-tracked changes (`session.add()`/`instance.delete()`) go
through these events - a bulk `Model.query.filter(...).delete()`/
`.update()` bypasses them, same as any other SQLAlchemy session event.
This can leave a stale entry in the index, but never a wrong search
result: `search()` always re-verifies matches against the database, so
a stale id simply stops resolving to a row. `reindex()` clears it up.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import os
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from itertools import chain
from typing import Any, override

import tantivy
from flask import Flask
from flask_sqlalchemy.model import Model
from sqlalchemy import Select, case, event, select
from sqlalchemy import false as sql_false

from flaskbb.core.search.base import ModelT, SearchBackend
from flaskbb.extensions import db
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.user.models import User

_SEARCH_LIMIT = 1000
_STASH_KEY = "flaskbb_tantivy_pending"


@dataclass(frozen=True)
class _ModelSpec:
    model: ModelT
    text: Callable[[Any], str]


def _joined(*parts: Any) -> str:
    return " ".join(str(p) for p in parts if p)


def _post_text(post: Post) -> str:
    return _joined(post.username, post.modified_by, post.content)


def _topic_text(topic: Topic) -> str:
    return _joined(
        topic.title, topic.username, getattr(topic.first_post, "content", None)
    )


def _forum_text(forum: Forum) -> str:
    return _joined(forum.title, forum.description)


def _user_text(user: User) -> str:
    return _joined(user.username, user.email)


_SPECS: tuple[_ModelSpec, ...] = (
    _ModelSpec(Post, _post_text),
    _ModelSpec(Topic, _topic_text),
    _ModelSpec(Forum, _forum_text),
    _ModelSpec(User, _user_text),
)


def _build_schema() -> "tantivy.Schema":
    builder = tantivy.SchemaBuilder()
    builder.add_integer_field("pk", stored=True, indexed=True, fast=True)
    builder.add_text_field("text", stored=False)
    return builder.build()


# Module-level so SQLAlchemy session events (registered once, on the
# single shared db.session) can dispatch to whichever backend instance
# is currently registered - see module docstring.
_active: "TantivyBackend | None" = None
_session_events_registered = False


def _after_flush(session: Any, flush_context: Any) -> None:
    # Fires once this flush's INSERT/UPDATE/DELETE statements have run -
    # autoincrement pks are populated by now (before_commit fires
    # *before* the flush, so pks aren't assigned yet there). Still
    # pre-COMMIT, so a rolled-back transaction never reaches this data.
    # session.new/dirty/deleted still list this flush's objects here;
    # by after_flush_postexec they've already been reclassified as
    # persistent/detached and the collections are empty. A single
    # commit() can trigger more than one flush, so pending writes
    # accumulate in session.info across calls rather than overwrite.
    if _active is None:
        return
    pending = session.info.setdefault(_STASH_KEY, {"write": [], "remove": []})
    for obj in chain(session.new, session.dirty):
        spec = _active._spec_by_model.get(type(obj))
        if spec is not None:
            pending["write"].append((spec.model, obj.id, spec.text(obj)))
    for obj in session.deleted:
        spec = _active._spec_by_model.get(type(obj))
        if spec is not None:
            pending["remove"].append((spec.model, obj.id))


def _after_commit(session: Any) -> None:
    pending = session.info.pop(_STASH_KEY, None)
    if pending and _active is not None:
        _active._apply_pending(pending)


def _after_rollback(session: Any) -> None:
    session.info.pop(_STASH_KEY, None)


def _register_session_events() -> None:
    global _session_events_registered
    if _session_events_registered:
        return
    event.listen(db.session, "after_flush", _after_flush)
    event.listen(db.session, "after_commit", _after_commit)
    event.listen(db.session, "after_rollback", _after_rollback)
    _session_events_registered = True


class TantivyBackend(SearchBackend):
    """Full-text search backed by a per-model Tantivy index on disk."""

    @override
    def init_app(self, app: Flask) -> None:
        global _active

        index_dir = app.config["SEARCH_INDEX_DIR"]
        self._spec_by_model: dict[ModelT, _ModelSpec] = {
            spec.model: spec for spec in _SPECS
        }
        self._indexes: dict[ModelT, tantivy.Index] = {}
        self._writers: dict[ModelT, tantivy.IndexWriter] = {}

        for spec in _SPECS:
            model_dir = os.path.join(index_dir, spec.model.__name__.lower())
            os.makedirs(model_dir, exist_ok=True)
            index = tantivy.Index(_build_schema(), path=model_dir)
            self._indexes[spec.model] = index
            self._writers[spec.model] = index.writer()

        _active = self
        _register_session_events()

    def _spec_for(self, instance: Model) -> _ModelSpec:
        spec = self._spec_by_model.get(type(instance))
        if spec is None:
            raise ValueError(f"{type(instance).__name__} is not a searchable model")
        return spec

    @override
    def index(self, instance: Any) -> None:
        spec = self._spec_for(instance)
        writer = self._writers[spec.model]
        writer.delete_documents_by_term("pk", instance.id)
        writer.add_document(tantivy.Document(pk=instance.id, text=spec.text(instance)))
        writer.commit()

    @override
    def update(self, instance: Any) -> None:
        # Tantivy has no upsert; re-indexing is always delete-then-add,
        # which is exactly what index() already does.
        self.index(instance)

    @override
    def remove(self, instance: Any) -> None:
        spec = self._spec_for(instance)
        writer = self._writers[spec.model]
        writer.delete_documents_by_term("pk", instance.id)
        writer.commit()

    def _apply_pending(self, pending: dict[str, list[Any]]) -> None:
        touched: set[ModelT] = set()
        for model, pk, text in pending["write"]:
            writer = self._writers[model]
            writer.delete_documents_by_term("pk", pk)
            writer.add_document(tantivy.Document(pk=pk, text=text))
            touched.add(model)
        for model, pk in pending["remove"]:
            writer = self._writers[model]
            writer.delete_documents_by_term("pk", pk)
            touched.add(model)
        for model in touched:
            self._writers[model].commit()

    @override
    def reindex(self, models: Sequence[ModelT] | None = None) -> None:
        specs = _SPECS if models is None else [s for s in _SPECS if s.model in models]
        for spec in specs:
            writer = self._writers[spec.model]
            writer.delete_all_documents()
            rows = db.session.execute(db.select(spec.model)).unique().scalars()
            for instance in rows:
                writer.add_document(
                    tantivy.Document(pk=instance.id, text=spec.text(instance))
                )
            writer.commit()

    @override
    def search(self, model: ModelT, query: str) -> Select[Any]:
        spec = self._spec_by_model.get(model)
        if spec is None:
            raise ValueError(f"{model.__name__} is not a searchable model")

        index = self._indexes[model]
        # A searcher only reflects writes as of its index's last reload();
        # commits from this backend's own writer don't trigger it
        # automatically, so it's called explicitly before every search.
        index.reload()
        parsed, _errors = index.parse_query_lenient(query, ["text"])
        searcher = index.searcher()
        result = searcher.search(parsed, limit=_SEARCH_LIMIT)

        pks = [searcher.doc(addr).to_dict()["pk"][0] for _score, addr in result.hits]
        # ModelT is bound to flask_sqlalchemy's generic Model, which
        # doesn't declare an `id` attribute - all our indexed models have an 'id'
        # as primary key, hence getattr() over `model.id`.
        pk_col = getattr(model, "id")

        if not pks:
            return select(model).where(sql_false())

        ordering = case({pk: rank for rank, pk in enumerate(pks)}, value=pk_col)
        return select(model).where(pk_col.in_(pks)).order_by(ordering)
