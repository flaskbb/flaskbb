"""add full-text search indexes

Adds the database-native search index the "postgresql" and "sqlite"
SEARCH_BACKENDs rely on, branching on the connected dialect:

- PostgreSQL: a generated `search_vector` (tsvector) column plus a GIN
  index on each searchable table.
- SQLite: an external-content FTS5 virtual table per searchable table,
  kept in sync by AFTER INSERT/UPDATE/DELETE triggers, backfilled via
  FTS5's 'rebuild'.

On any other dialect (e.g. MySQL) this is a no-op - those deployments
use the dialect-agnostic "sql" ILIKE backend instead.

The per-dialect DDL is exposed as pure statement-list functions
(`sqlite_upgrade_sql` etc.) so the test suite can apply the same schema
to its create_all()'d database without duplicating the SQL.

Revision ID: 1784625534
Revises: 1784020734
Create Date: 2026-07-21 15:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "1784625534"
down_revision = "1784020734"
branch_labels = ()
depends_on = None

# (table, indexed columns) - mirrors the field mapping the search
# backends use. Nullable columns are coalesced to '' when indexed.
_TABLES = [
    ("posts", ["username", "modified_by", "content"]),
    ("topics", ["title", "username"]),
    ("forums", ["title", "description"]),
    ("users", ["username", "email"]),
]


def postgresql_upgrade_sql():
    stmts = []
    for table, cols in _TABLES:
        expr = " || ' ' || ".join(f"coalesce({col}, '')" for col in cols)
        stmts.append(
            f"ALTER TABLE {table} ADD COLUMN search_vector tsvector "
            f"GENERATED ALWAYS AS (to_tsvector('english', {expr})) STORED"
        )
        stmts.append(f"CREATE INDEX ix_{table}_search_vector ON {table} USING gin (search_vector)")
    return stmts


def postgresql_downgrade_sql():
    stmts = []
    for table, _cols in _TABLES:
        stmts.append(f"DROP INDEX IF EXISTS ix_{table}_search_vector")
        stmts.append(f"ALTER TABLE {table} DROP COLUMN IF EXISTS search_vector")
    return stmts


def sqlite_upgrade_sql():
    stmts = []
    for table, cols in _TABLES:
        fts = f"{table}_fts"
        collist = ", ".join(cols)
        new_vals = ", ".join(f"new.{col}" for col in cols)
        old_vals = ", ".join(f"old.{col}" for col in cols)

        stmts.append(
            f"CREATE VIRTUAL TABLE {fts} USING fts5("
            f"{collist}, content='{table}', content_rowid='id')"
        )
        stmts.append(
            f"CREATE TRIGGER {table}_ai AFTER INSERT ON {table} BEGIN "
            f"INSERT INTO {fts}(rowid, {collist}) VALUES (new.id, {new_vals}); END"
        )
        stmts.append(
            f"CREATE TRIGGER {table}_ad AFTER DELETE ON {table} BEGIN "
            f"INSERT INTO {fts}({fts}, rowid, {collist}) "
            f"VALUES ('delete', old.id, {old_vals}); END"
        )
        stmts.append(
            f"CREATE TRIGGER {table}_au AFTER UPDATE ON {table} BEGIN "
            f"INSERT INTO {fts}({fts}, rowid, {collist}) "
            f"VALUES ('delete', old.id, {old_vals}); "
            f"INSERT INTO {fts}(rowid, {collist}) VALUES (new.id, {new_vals}); END"
        )
        stmts.append(f"INSERT INTO {fts}({fts}) VALUES ('rebuild')")
    return stmts


def sqlite_downgrade_sql():
    stmts = []
    for table, _cols in _TABLES:
        fts = f"{table}_fts"
        stmts.append(f"DROP TRIGGER IF EXISTS {table}_ai")
        stmts.append(f"DROP TRIGGER IF EXISTS {table}_ad")
        stmts.append(f"DROP TRIGGER IF EXISTS {table}_au")
        stmts.append(f"DROP TABLE IF EXISTS {fts}")
    return stmts


def upgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        statements = postgresql_upgrade_sql()
    elif dialect == "sqlite":
        statements = sqlite_upgrade_sql()
    else:
        return
    for statement in statements:
        op.execute(statement)


def downgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        statements = postgresql_downgrade_sql()
    elif dialect == "sqlite":
        statements = sqlite_downgrade_sql()
    else:
        return
    for statement in statements:
        op.execute(statement)
