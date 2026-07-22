# -*- coding: utf-8 -*-
"""
flaskbb.core.search.base
~~~~~~~~~~~~~~~~~~~~~~~~

The pluggable search backend abstraction. A backend owns three
responsibilities:
    - keeping whatever index it needs in sync (index/update/remove/reindex)
    - answering search queries with a `select(model)` statement that
      returns a SQLAlchemy Model instance
    - producing a highlighted preview of a matched row's content (snippet)

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import re
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from flask import Flask
from flask_sqlalchemy.model import Model
from markupsafe import Markup, escape
from sqlalchemy import Select, case, select
from sqlalchemy import false as sql_false

ModelT = type[Model]


def ordered_by_ids(model: ModelT, ids: Sequence[int]) -> Select[Any]:
    """Build a `select(model)` restricted to `ids` and ordered to match
    their sequence - the shared shape every index-backed backend returns
    from `search()` once it has resolved a ranked list of primary keys.
    An empty `ids` yields a statement that matches nothing.
    """
    # ModelT is bound to flask_sqlalchemy's generic Model, which doesn't
    # declare an `id` attribute - all searchable models use `id` as pk.
    pk_col = getattr(model, "id")
    if not ids:
        return select(model).where(sql_false())
    ordering = case({pk: rank for rank, pk in enumerate(ids)}, value=pk_col)
    return select(model).where(pk_col.in_(ids)).order_by(ordering)


class SearchBackend(ABC):
    """Pluggable full-text/attribute search over FlaskBB models."""

    def init_app(self, app: Flask) -> None:
        """Register this backend on the app."""

    @abstractmethod
    def index(self, instance: Model) -> None:
        """Add a newly created `instance` to the index. No-op for
        backends where the row itself is the index.
        """

    @abstractmethod
    def update(self, instance: Model) -> None:
        """Refresh the index entry for an already-indexed `instance`."""

    @abstractmethod
    def remove(self, instance: Model) -> None:
        """Remove `instance` from the index (e.g. on delete)."""

    @abstractmethod
    def search(self, model: ModelT, query: str) -> Select[Any]:
        """Return a `select(model)` statement matching `query`,
        best-effort ordered by relevance. Callers execute it themselves
        (`db.session.scalars(stmt).unique().all()`) or paginate it
        (`db.paginate(stmt, ...)`) - either way it must yield full
        SQLAlchemy Model instances.

        Raises `ValueError` if `model` is not a searchable model for
        this backend.
        """

    def search_multi(
        self, models: Mapping[str, ModelT], query: str
    ) -> dict[str, Select[Any]]:
        """Search several models at once. `models` maps a result-dict key
        ("post", "topic", "forum", "user") to the model class. Returns a
        dict containing only the given keys, each mapped to the same
        kind of statement `search()` returns. Default implementation
        just calls `search()` for each model; backends that can do a
        single cross-model query may override this.
        """
        return {key: self.search(model, query) for key, model in models.items()}

    @abstractmethod
    def reindex(self, models: Sequence[ModelT] | None = None) -> None:
        """Rebuild the index for `models` (default: all models this
        backend knows about).
        """

    def snippet(self, model: ModelT, pk: int, content: str, query: str) -> Markup:
        """Returns an HTML preview of `content` around the first match of
        `query`, bounded to roughly the `SEARCH_SNIPPET_LENGTH` setting
        (0 means the full content, unbounded). The match itself is
        wrapped in `<mark>`.

        `model`/`pk` identify the row `content` was taken from, for
        backends that can produce a smarter, index-aware preview (e.g.
        one that accounts for stemming/tokenization) by looking the row
        up in their own index. This default implementation ignores both
        and just does a literal, case-insensitive substring search - it's
        optional to override, so backends that don't need anything
        smarter (or can't) get a correct-enough preview for free.
        """
        # deferred: flaskbb.core.settings -> ... -> flaskbb.extensions ->
        # flaskbb.core.search, a circular import at module level.
        from flaskbb.core.settings import flaskbb_config

        length = flaskbb_config["SEARCH_SNIPPET_LENGTH"]

        match = re.search(re.escape(query), content, re.IGNORECASE) if query else None
        if match is None:
            text = content if not length else content[:length]
            return Markup(escape(text))

        if not length:
            start, end = 0, len(content)
        else:
            half = length // 2
            start = max(0, match.start() - half)
            end = min(len(content), match.end() + half)

        prefix = "…" if start > 0 else ""
        suffix = "…" if end < len(content) else ""
        before = escape(content[start : match.start()])
        matched = escape(content[match.start() : match.end()])
        after = escape(content[match.end() : end])

        return Markup(f"{prefix}{before}<mark>{matched}</mark>{after}{suffix}")


@dataclass(frozen=True)
class SearchBackendRegistration:
    """Maps a `SEARCH_BACKEND` config name to a backend implementation.

    Returned by the `flaskbb_load_search_backends` plugin hook so a plugin
    can add its own backend under a new name. `name` must not collide with
    a built-in ("sql", "postgresql", "sqlite") or another plugin's backend.
    """

    name: str
    backend: type[SearchBackend]
