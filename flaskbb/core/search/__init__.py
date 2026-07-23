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
from typing import TYPE_CHECKING, Any, override

from flask import Flask
from flask_sqlalchemy.model import Model
from markupsafe import Markup
from sqlalchemy import Select

from flaskbb.core.search.base import (
    ModelT,
    SearchBackend,
    SearchBackendRegistration,
)

if TYPE_CHECKING:
    from flaskbb.plugins.manager import FlaskBBPluginManager

__all__ = ["FlaskBBSearch", "SearchBackend", "SearchBackendRegistration"]

_CORE_BACKENDS = ("sql", "postgresql", "sqlite")


def _resolve_core(name: str) -> type[SearchBackend] | None:
    # Lazily import only the selected built-in: importing a backend module
    # also registers its create_all DDL, so unused ones stay out of the way.
    if name == "sql":
        from flaskbb.core.search.backends.sql import SQLSearchBackend

        return SQLSearchBackend
    if name == "postgresql":
        from flaskbb.core.search.backends.postgresql import PostgreSQLSearchBackend

        return PostgreSQLSearchBackend
    if name == "sqlite":
        from flaskbb.core.search.backends.sqlite import SQLiteSearchBackend

        return SQLiteSearchBackend
    return None


def _plugin_backends(
    plugin_manager: "FlaskBBPluginManager",
) -> dict[str, type[SearchBackend]]:
    """Collect backends contributed via the `flaskbb_load_search_backends`
    hook into a `{name: class}` dict. A name that collides with a built-in
    or with another plugin's backend raises `ValueError`.
    """
    registry: dict[str, type[SearchBackend]] = {}
    for result in plugin_manager.hook.flaskbb_load_search_backends():
        regs = result if isinstance(result, (list, tuple)) else [result]
        for reg in regs:
            if reg.name in _CORE_BACKENDS:
                raise ValueError(
                    f"Search backend {reg.name!r} is a built-in and cannot be "
                    f"registered by a plugin."
                )
            if reg.name in registry:
                raise ValueError(
                    f"Search backend {reg.name!r} is registered by more than "
                    f"one plugin."
                )
            registry[reg.name] = reg.backend
    return registry


class FlaskBBSearch(SearchBackend):
    def __init__(self, plugin_manager: "FlaskBBPluginManager | None" = None) -> None:
        # plugin_manager is injected (see flaskbb/extensions.py) rather than
        # imported, to avoid a core.search <-> extensions import cycle -
        # the same dependency-injection the settings registry uses.
        self._impl: SearchBackend | None = None
        self._plugin_manager = plugin_manager

    @override
    def init_app(self, app: Flask) -> None:
        """Resolve and initialize the configured backend. Must run after
        plugins are loaded so `flaskbb_load_search_backends` contributions
        are available (see `configure_search_backend` in flaskbb/app.py).
        """
        name = app.config.get("SEARCH_BACKEND", "sql")
        # Always collected, so a plugin colliding with a built-in is caught
        # even when that built-in is the backend actually selected.
        plugins = (
            _plugin_backends(self._plugin_manager)
            if self._plugin_manager is not None
            else {}
        )
        backend_cls = _resolve_core(name) or plugins.get(name)
        if backend_cls is None:
            choices = sorted({*_CORE_BACKENDS, *plugins})
            raise ValueError(f"Unknown SEARCH_BACKEND {name!r}; choices: {choices}")
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
