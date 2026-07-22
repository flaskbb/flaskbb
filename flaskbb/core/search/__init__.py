# -*- coding: utf-8 -*-
"""
flaskbb.core.search
~~~~~~~~~~~~~~~~~~~~

Pluggable full-text search for FlaskBB. It selects the backend that has
been set in the config `SEARCH_BACKEND`.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections.abc import Mapping, Sequence
from typing import Any, override

from flask import Flask
from flask_sqlalchemy.model import Model
from markupsafe import Markup
from sqlalchemy import Select

from flaskbb.core.search.base import ModelT, SearchBackend

_KNOWN_BACKENDS = ("sql", "postgresql", "sqlite")


def _resolve_backend_class(name: str) -> type[SearchBackend]:
    # circular dependency
    if name == "sql":
        from flaskbb.core.search.sql import SQLSearchBackend

        return SQLSearchBackend
    if name == "postgresql":
        from flaskbb.core.search.postgresql import PostgreSQLSearchBackend

        return PostgreSQLSearchBackend
    if name == "sqlite":
        from flaskbb.core.search.sqlite import SQLiteSearchBackend

        return SQLiteSearchBackend
    raise ValueError(
        f"Unknown SEARCH_BACKEND {name!r}; choices: {list(_KNOWN_BACKENDS)}"
    )


class FlaskBBSearch(SearchBackend):
    def __init__(self) -> None:
        self._impl: SearchBackend | None = None

    @override
    def init_app(self, app: Flask) -> None:
        """Set the extension up and register the backend on the extension."""
        name = app.config.get("SEARCH_BACKEND", "sql")
        backend_cls = _resolve_backend_class(name)
        self._impl = backend_cls()
        self._impl.init_app(app)

    def _get_impl(self) -> SearchBackend:
        if self._impl is None:
            raise RuntimeError("flaskbb_search.init_app(app) was not called")
        return self._impl

    @override
    def index(self, instance: Model) -> None:
        self._get_impl().index(instance)

    @override
    def update(self, instance: Model) -> None:
        self._get_impl().update(instance)

    @override
    def remove(self, instance: Model) -> None:
        self._get_impl().remove(instance)

    @override
    def search(self, model: ModelT, query: str) -> Select[Any]:
        return self._get_impl().search(model, query)

    @override
    def search_multi(
        self, models: Mapping[str, ModelT], query: str
    ) -> dict[str, Select[Any]]:
        return self._get_impl().search_multi(models, query)

    @override
    def reindex(self, models: Sequence[ModelT] | None = None) -> None:
        self._get_impl().reindex(models)

    @override
    def snippet(self, model: ModelT, pk: int, content: str, query: str) -> Markup:
        return self._get_impl().snippet(model, pk, content, query)
