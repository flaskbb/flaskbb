# -*- coding: utf-8 -*-
"""
flaskbb.core.search.base
~~~~~~~~~~~~~~~~~~~~~~~~

The pluggable search backend abstraction. A backend owns two
responsibilities:
    - keeping whatever index it needs in sync (index/update/remove/reindex)
    - and answering search queries with a `select(model)` statement that
      returns a SQLAlchemy Model instance.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from flask import Flask
from flask_sqlalchemy.model import Model
from sqlalchemy import Select

ModelT = type[Model]


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
