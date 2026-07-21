# -*- coding: utf-8 -*-
"""
flaskbb.core.search.tantivy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A search backend built on Tantivy (a Rust full-text search engine).
Each searchable model gets its own on-disk Tantivy index (under `SEARCH_INDEX_DIR`),
keyed on the model's primary key plus three tokenized text fields: `title`,
`username` and `content`. `content` is the only one stored in the index
(the other two are indexed for matching only) - it holds each model's
actual body text (`Post.content`/`Topic.first_post.content`/...), so
`snippet()` can generate a preview straight from the index via Tantivy's
own `SnippetGenerator`, without a round-trip back to the database.

The index is kept in sync via via SQLAlchemy session events `after_flush`,
`after_commit` and `after_rollback`.

However, only ORM-tracked changes (`session.add()`/`instance.delete()`) go
through these events - a bulk `Model.query.filter(...).delete()`/
`.update()` bypasses them, same as any other SQLAlchemy session event.
This can leave a stale entry in the index, but never a wrong search
result: `search()` always re-verifies matches against the database, so
a stale id simply stops resolving to a row. `reindex()` clears it up.

Tantivy allows only one `IndexWriter` per index directory per process,
so a multi-process deployment can't have every process open its own
writer. `SEARCH_INDEX_WRITER` (config) says whether *this* process owns
the writers - exactly one process (a Celery worker) should set it True;
every other process (e.g. every web worker) sets it False and gets
read-only `Index`/`Searcher` objects only. On a writer-less process,
`_after_commit` dispatches the pending writes to the writer process as
a Celery task (`_apply_pending_task`, on the "search" queue - a worker
can consume it alongside other queues like the default one used for
email) instead of applying them locally; `index()`/`update()`/
`remove()`/`reindex()` raise if called directly there, since there's no
local writer to use.

The writer process must run with `--pool=solo`: prefork (the default
pool) forks worker children *after* `IndexWriter` has already spawned
Tantivy's own internal indexing threads, and forking a process with
live native threads is unsafe. That applies to the whole worker
process, not per-queue, so a single worker consuming both "search" and
the default queue runs everything - email included - through the solo
pool (sequential, no concurrency). Split into two worker processes,
each consuming one queue with its own `--pool`, if that becomes a
throughput problem.

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
from markupsafe import Markup
from sqlalchemy import Select, case, event, select
from sqlalchemy import false as sql_false

from flaskbb.core.search.base import ModelT, SearchBackend
from flaskbb.core.settings import flaskbb_config
from flaskbb.extensions import celery, db
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.user.models import User

_SEARCH_LIMIT = 1000
_STASH_KEY = "flaskbb_tantivy_pending"
_FIELDS = ("title", "username", "content")


@dataclass(frozen=True)
class _ModelSpec:
    model: ModelT
    # (title, username, content) - `content` is the field previews/snippets
    # are generated from, so it must always be the actual body text
    # (`Post.content`/`Topic.first_post.content`), never blank if avoidable.
    fields: Callable[[Any], tuple[str, str, str]]


def _joined(*parts: Any) -> str:
    return " ".join(str(p) for p in parts if p)


def _document(pk: int, fields: tuple[str, str, str]) -> "tantivy.Document":
    title, username, content = fields
    return tantivy.Document(pk=pk, title=title, username=username, content=content)


def _post_fields(post: Post) -> tuple[str, str, str]:
    return ("", _joined(post.username, post.modified_by), post.content or "")


def _topic_fields(topic: Topic) -> tuple[str, str, str]:
    return (
        topic.title,
        topic.username,
        getattr(topic.first_post, "content", None) or "",
    )


def _forum_fields(forum: Forum) -> tuple[str, str, str]:
    return (forum.title, "", forum.description or "")


def _user_fields(user: User) -> tuple[str, str, str]:
    return ("", _joined(user.username, user.email), "")


_SPECS: tuple[_ModelSpec, ...] = (
    _ModelSpec(Post, _post_fields),
    _ModelSpec(Topic, _topic_fields),
    _ModelSpec(Forum, _forum_fields),
    _ModelSpec(User, _user_fields),
)


def _build_schema() -> "tantivy.Schema":
    builder = tantivy.SchemaBuilder()
    builder.add_integer_field("pk", stored=True, indexed=True, fast=True)
    builder.add_text_field("title", stored=False)
    builder.add_text_field("username", stored=False)
    # stored so `snippet()` can generate a preview straight from the
    # index, without needing the DB row's content passed back in.
    builder.add_text_field("content", stored=True)
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
            pending["write"].append((spec.model, obj.id, spec.fields(obj)))
    for obj in session.deleted:
        spec = _active._spec_by_model.get(type(obj))
        if spec is not None:
            pending["remove"].append((spec.model, obj.id))


_MODEL_BY_NAME: dict[str, ModelT] = {spec.model.__name__: spec.model for spec in _SPECS}


def _serialize_pending(pending: dict[str, list[Any]]) -> dict[str, list[Any]]:
    return {
        "write": [
            (model.__name__, pk, fields) for model, pk, fields in pending["write"]
        ],
        "remove": [(model.__name__, pk) for model, pk in pending["remove"]],
    }


def _deserialize_pending(payload: dict[str, list[Any]]) -> dict[str, list[Any]]:
    return {
        "write": [
            (_MODEL_BY_NAME[name], pk, tuple(fields))
            for name, pk, fields in payload["write"]
        ],
        "remove": [(_MODEL_BY_NAME[name], pk) for name, pk in payload["remove"]],
    }


@celery.task(queue="search")
def _apply_pending_task(payload: dict[str, list[Any]]) -> None:
    # Runs on the Celery worker that owns the writers (SEARCH_INDEX_WRITER
    # is True there), dispatched from a process that has none - see
    # module docstring.
    if _active is not None:
        _active._apply_pending(_deserialize_pending(payload))


def _after_commit(session: Any) -> None:
    pending = session.info.pop(_STASH_KEY, None)
    if _active is None or not pending or not (pending["write"] or pending["remove"]):
        return
    if _active._can_write:
        _active._apply_pending(pending)
    else:
        _apply_pending_task.delay(_serialize_pending(pending))


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
        self._can_write: bool = app.config["SEARCH_INDEX_WRITER"]
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
            if self._can_write:
                self._writers[spec.model] = index.writer()

        _active = self
        _register_session_events()

    def _require_writer(self) -> None:
        if not self._can_write:
            raise RuntimeError(
                "This process has SEARCH_INDEX_WRITER=False; it holds no "
                "Tantivy IndexWriter. Writes made through the ORM are "
                "dispatched to the writer process as a Celery task "
                "instead - call this on that process/config."
            )

    def _spec_for(self, instance: Model) -> _ModelSpec:
        spec = self._spec_by_model.get(type(instance))
        if spec is None:
            raise ValueError(f"{type(instance).__name__} is not a searchable model")
        return spec

    @override
    def index(self, instance: Any) -> None:
        self._require_writer()
        spec = self._spec_for(instance)
        writer = self._writers[spec.model]
        writer.delete_documents_by_term("pk", instance.id)
        writer.add_document(_document(instance.id, spec.fields(instance)))
        writer.commit()

    @override
    def update(self, instance: Any) -> None:
        # Tantivy has no upsert; re-indexing is always delete-then-add,
        # which is exactly what index() already does.
        self.index(instance)

    @override
    def remove(self, instance: Any) -> None:
        self._require_writer()
        spec = self._spec_for(instance)
        writer = self._writers[spec.model]
        writer.delete_documents_by_term("pk", instance.id)
        writer.commit()

    def _apply_pending(self, pending: dict[str, list[Any]]) -> None:
        touched: set[ModelT] = set()
        for model, pk, fields in pending["write"]:
            writer = self._writers[model]
            writer.delete_documents_by_term("pk", pk)
            writer.add_document(_document(pk, fields))
            touched.add(model)
        for model, pk in pending["remove"]:
            writer = self._writers[model]
            writer.delete_documents_by_term("pk", pk)
            touched.add(model)
        for model in touched:
            self._writers[model].commit()

    @override
    def reindex(self, models: Sequence[ModelT] | None = None) -> None:
        self._require_writer()
        specs = _SPECS if models is None else [s for s in _SPECS if s.model in models]
        for spec in specs:
            writer = self._writers[spec.model]
            writer.delete_all_documents()
            rows = db.session.execute(db.select(spec.model)).unique().scalars()
            for instance in rows:
                writer.add_document(_document(instance.id, spec.fields(instance)))
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
        parsed, _errors = index.parse_query_lenient(query, list(_FIELDS))
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

    @override
    def snippet(self, model: ModelT, pk: int, content: str, query: str) -> Markup:
        length = flaskbb_config["SEARCH_SNIPPET_LENGTH"]
        spec = self._spec_by_model.get(model)
        if spec is None or not length:
            # Unknown model, or SEARCH_SNIPPET_LENGTH == 0 ("show the
            # full content") - Tantivy's snippet generator always bounds
            # its output, so there's no native way to honor that; fall
            # back to the generic implementation instead.
            return super().snippet(model, pk, content, query)

        index = self._indexes[model]
        index.reload()
        schema = index.schema
        searcher = index.searcher()

        pk_query = tantivy.Query.term_query(schema, "pk", pk)
        hits = searcher.search(pk_query, limit=1).hits
        if not hits:
            return super().snippet(model, pk, content, query)

        doc = searcher.doc(hits[0][1])
        parsed, _errors = index.parse_query_lenient(query, list(_FIELDS))
        generator = tantivy.SnippetGenerator.create(searcher, parsed, schema, "content")
        generator.set_max_num_chars(length)

        html = generator.snippet_from_doc(doc).to_html()
        if not html:
            # The match was in `title`/`username`, not `content` - nothing
            # to highlight in the content preview itself.
            return super().snippet(model, pk, content, query)

        return Markup(html.replace("<b>", "<mark>").replace("</b>", "</mark>"))
