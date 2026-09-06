"""
flaskbb.core.search.backends.sqlite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A search backend built on SQLite's FTS5 full-text extension. Each
searchable table gets an external-content FTS5 virtual table (e.g.
`posts_fts` over `posts`) plus AFTER INSERT/UPDATE/DELETE triggers that
keep it in sync.

The schema is created two ways: `flaskbb db upgrade` runs the migration
(for existing installs), and a fresh install's `db.create_all()` builds
it via the `after_create` DDL registered below.

`search()` runs a bm25-ranked MATCH query to resolve primary keys and
returns the shared ordered `select(model)` statement (see
`ordered_by_ids`), so callers layer their permission/date filters on top.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import re
from collections.abc import Sequence
from typing import Any, override

from flask import current_app
from flask_sqlalchemy.model import Model
from sqlalchemy import DDL, event, Select, text

from flaskbb.core.search.base import ModelT, ordered_by_ids, SearchBackend
from flaskbb.core.search.spec import INDEX_SPECS
from flaskbb.extensions import db
from flaskbb.forum.models import Topic

_SEARCH_LIMIT = 1000

# model -> FTS virtual table name (`<table>_fts`).
_FTS_TABLES: dict[ModelT, str] = {model: f"{table}_fts" for model, table, _cols in INDEX_SPECS}


def _fts_query(query: str) -> str:
    """Turn arbitrary user input into a safe FTS5 MATCH expression:
    extract word tokens and quote each as a string, joined by spaces
    (implicit AND). Quoting keeps FTS5 operator characters in the input
    from being parsed as query syntax. Returns "" when there's nothing
    to match on.
    """
    tokens = re.findall(r"\w+", query, re.UNICODE)
    return " ".join(f'"{token}"' for token in tokens)


def _create_statements(table: str, cols: tuple[str, ...]) -> list[str]:
    fts = f"{table}_fts"
    collist = ", ".join(cols)
    new_vals = ", ".join(f"new.{col}" for col in cols)
    old_vals = ", ".join(f"old.{col}" for col in cols)
    return [
        f"CREATE VIRTUAL TABLE IF NOT EXISTS {fts} USING fts5("
        f"{collist}, content='{table}', content_rowid='id')",
        f"CREATE TRIGGER IF NOT EXISTS {table}_ai AFTER INSERT ON {table} BEGIN "
        f"INSERT INTO {fts}(rowid, {collist}) VALUES (new.id, {new_vals}); END",
        f"CREATE TRIGGER IF NOT EXISTS {table}_ad AFTER DELETE ON {table} BEGIN "
        f"INSERT INTO {fts}({fts}, rowid, {collist}) "
        f"VALUES ('delete', old.id, {old_vals}); END",
        f"CREATE TRIGGER IF NOT EXISTS {table}_au AFTER UPDATE ON {table} BEGIN "
        f"INSERT INTO {fts}({fts}, rowid, {collist}) "
        f"VALUES ('delete', old.id, {old_vals}); "
        f"INSERT INTO {fts}(rowid, {collist}) VALUES (new.id, {new_vals}); END",
        f"INSERT INTO {fts}({fts}) VALUES ('rebuild')",
    ]


def _emit_on_create(
    ddl: Any, target: Any, bind: Any, tables: Any = None, state: Any = None, **kw: Any
) -> bool:
    # Only build the FTS5 schema when create_all() runs against a SQLite
    # database with this backend actually selected - so a create_all() on
    # any other backend (e.g. the sql test suite) leaves these
    # tables untouched.
    if bind.dialect.name != "sqlite":
        return False
    try:
        return current_app.config.get("SEARCH_BACKEND") == "sqlite"  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    except RuntimeError:
        return False


def _register_create_all_ddl() -> None:
    for model, table, cols in INDEX_SPECS:
        for statement in _create_statements(table, cols):
            event.listen(
                model.__table__,
                "after_create",
                DDL(statement).execute_if(callable_=_emit_on_create),
            )


_register_create_all_ddl()


class SQLiteSearchBackend(SearchBackend):
    """Full-text search backed by SQLite FTS5 virtual tables."""

    @override
    def index(self, instance: Model) -> None:
        pass

    @override
    def update(self, instance: Model) -> None:
        pass

    @override
    def remove(self, instance: Model) -> None:
        pass

    @override
    def reindex(self, models: Sequence[ModelT] | None = None) -> None:
        tables = (
            _FTS_TABLES.values()
            if models is None
            else [_FTS_TABLES[m] for m in models if m in _FTS_TABLES]
        )
        for fts in tables:
            db.session.execute(text(f"INSERT INTO {fts}({fts}) VALUES ('rebuild')"))
        db.session.commit()

    def _ranked_ids(self, fts: str, fts_query: str) -> list[int]:
        # `fts` is an internal constant, never user input. bm25() returns
        # a lower score for better matches, so ascending order is best-first.
        stmt = text(f"SELECT rowid FROM {fts} WHERE {fts} MATCH :q ORDER BY bm25({fts}) LIMIT :lim")
        rows = db.session.execute(stmt, {"q": fts_query, "lim": _SEARCH_LIMIT})
        return list(rows.scalars())

    def _topic_body_ids(self, fts_query: str) -> list[int]:
        # A topic also matches on its opening post's body (parity with the
        # `sql` backend), indexed in posts_fts.
        stmt = text(
            "SELECT t.id FROM topics t "
            "JOIN posts_fts ON posts_fts.rowid = t.first_post_id "
            "WHERE posts_fts MATCH :q ORDER BY bm25(posts_fts) LIMIT :lim"
        )
        rows = db.session.execute(stmt, {"q": fts_query, "lim": _SEARCH_LIMIT})
        return list(rows.scalars())

    @override
    def search(self, model: ModelT, query: str) -> Select[Any]:
        fts = _FTS_TABLES.get(model)
        if fts is None:
            raise ValueError(f"{model.__name__} is not a searchable model")

        fts_query = _fts_query(query)
        if not fts_query:
            return ordered_by_ids(model, [])

        ids = self._ranked_ids(fts, fts_query)
        if model is Topic:
            seen = set(ids)
            ids += [pk for pk in self._topic_body_ids(fts_query) if pk not in seen]
        return ordered_by_ids(model, ids)
