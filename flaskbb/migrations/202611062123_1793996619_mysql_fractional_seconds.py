"""store fractional seconds on MySQL

UTCDateTime columns were plain DATETIME on MySQL and MariaDB, which keep
whole seconds, so a post written in the same second as a read mark did
not count as newer than it. The type now maps to DATETIME(6) there, and
this widens the existing columns. A no-op on every other dialect.

Revision ID: 1793996619
Revises: 1792002242
Create Date: 2026-11-06 21:23:39

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "1793996619"
down_revision = "1792002242"
branch_labels = ()
depends_on = None

COLUMNS = [
    ("attachments", "date_created"),
    ("forums", "last_post_created"),
    ("forumsread", "last_read"),
    ("forumsread", "cleared"),
    ("posts", "date_created"),
    ("posts", "date_modified"),
    ("posts", "hidden_at"),
    ("reports", "reported"),
    ("reports", "zapped"),
    ("topics", "date_created"),
    ("topics", "last_updated"),
    ("topics", "hidden_at"),
    ("topicsread", "last_read"),
    ("users", "date_joined"),
    ("users", "lastseen"),
    ("users", "last_failed_login"),
]


def _alter_mysql_columns(type_, existing_type):
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return
    inspector = sa.inspect(bind)
    for table, column in COLUMNS:
        nullable = next(c["nullable"] for c in inspector.get_columns(table) if c["name"] == column)
        op.alter_column(
            table,
            column,
            type_=type_,
            existing_type=existing_type,
            existing_nullable=nullable,
        )


def upgrade():
    _alter_mysql_columns(mysql.DATETIME(fsp=6), mysql.DATETIME())


def downgrade():
    _alter_mysql_columns(mysql.DATETIME(), mysql.DATETIME(fsp=6))
