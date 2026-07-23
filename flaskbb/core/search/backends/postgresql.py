# -*- coding: utf-8 -*-
"""
flaskbb.core.search.backends.postgresql
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A search backend built on PostgreSQL's native full-text search. Each
searchable table carries a `search_vector` column (`tsvector`, a
`GENERATED ALWAYS AS (...) STORED` column) with a GIN index over it, so
the index lives inside the same database as the data and is maintained
transactionally by PostgreSQL itself.

The schema is created two ways: `flaskbb db upgrade` runs the migration
(for existing installs), and a fresh install's `db.create_all()` builds
it via the `after_create` DDL registered below.

`search()` runs a ranked `plainto_tsquery`/`ts_rank` query to resolve a
list of primary keys and returns the shared ordered `select(model)`
statement (see `ordered_by_ids`), so callers add their permission/date
filters on top just as with every other backend.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections.abc import Sequence
from typing import Any, override

from flask import current_app
from flask_sqlalchemy.model import Model
from sqlalchemy import DDL, Select, event, func, literal_column, select
from sqlalchemy.dialects.postgresql import TSVECTOR

from flaskbb.core.search.base import ModelT, SearchBackend, ordered_by_ids
from flaskbb.core.search.spec import INDEX_SPECS, TABLES
from flaskbb.extensions import db
from flaskbb.forum.models import Post, Topic

_SEARCH_LIMIT = 1000
# The text search configuration used for both indexing (the generated
# search_vector column) and querying - the two must agree.
_TS_CONFIG = "english"


def _search_vector(table: str):
    # The generated search_vector column isn't declared on the ORM models
    # (kept dialect-agnostic), so it's referenced as a qualified literal
    # column - qualified because a topic-body query joins two tables that
    # both carry a search_vector.
    return literal_column(f"{table}.search_vector", type_=TSVECTOR)


def _create_statements(table: str, cols: tuple[str, ...]) -> list[str]:
    expr = " || ' ' || ".join(f"coalesce({col}, '')" for col in cols)
    return [
        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS search_vector tsvector "
        f"GENERATED ALWAYS AS (to_tsvector('{_TS_CONFIG}', {expr})) STORED",
        f"CREATE INDEX IF NOT EXISTS ix_{table}_search_vector "
        f"ON {table} USING gin (search_vector)",
    ]


def _emit_on_create(
    ddl: Any, target: Any, bind: Any, tables: Any = None, state: Any = None, **kw: Any
) -> bool:
    # Only build the tsvector schema when create_all() runs against a
    # PostgreSQL database with this backend actually selected - so a
    # create_all() on any other backend (e.g. the sql test suite)
    # leaves these tables untouched.
    if bind.dialect.name != "postgresql":
        return False
    try:
        return current_app.config.get("SEARCH_BACKEND") == "postgresql"
    except RuntimeError:
        return False


def _register_create_all_ddl() -> None:
    for model, table, cols in INDEX_SPECS:
        for statement in _create_statements(table, cols):
            event.listen(
                getattr(model, "__table__"),
                "after_create",
                DDL(statement).execute_if(callable_=_emit_on_create),
            )


_register_create_all_ddl()


class PostgreSQLSearchBackend(SearchBackend):
    """Full-text search backed by PostgreSQL `tsvector` columns."""

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
        pass

    def _ranked_ids(self, model: ModelT, table: str, query: str) -> list[int]:
        vector = _search_vector(table)
        tsquery = func.plainto_tsquery(_TS_CONFIG, query)
        pk_col = getattr(model, "id")
        stmt = (
            select(pk_col)
            .where(vector.op("@@")(tsquery))
            .order_by(func.ts_rank(vector, tsquery).desc())
            .limit(_SEARCH_LIMIT)
        )
        return list(db.session.scalars(stmt))

    def _topic_body_ids(self, query: str) -> list[int]:
        # A topic also matches on its opening post's body (parity with the
        # `sql` backend), which lives in `posts`, not `topics`.
        vector = _search_vector("posts")
        tsquery = func.plainto_tsquery(_TS_CONFIG, query)
        stmt = (
            select(Topic.id)
            .join(Post, Post.id == Topic.first_post_id)
            .where(vector.op("@@")(tsquery))
            .order_by(func.ts_rank(vector, tsquery).desc())
            .limit(_SEARCH_LIMIT)
        )
        return list(db.session.scalars(stmt))

    @override
    def search(self, model: ModelT, query: str) -> Select[Any]:
        table = TABLES.get(model)
        if table is None:
            raise ValueError(f"{model.__name__} is not a searchable model")
        if not query.strip():
            return ordered_by_ids(model, [])

        ids = self._ranked_ids(model, table, query)
        if model is Topic:
            seen = set(ids)
            ids += [pk for pk in self._topic_body_ids(query) if pk not in seen]
        return ordered_by_ids(model, ids)
