"""widen users.password for scrypt hashes and make plugin_registry.enabled,
posts.hidden, topics.hidden and users.post_count non-nullable

Revision ID: 1789335000
Revises: 1785759600
Create Date: 2026-09-13 21:30:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1789335000"
down_revision = "1785759600"
branch_labels = ()
depends_on = None

# FlaskBB 2.0 and 2.1 installed these columns via create_all() from models that
# still allowed NULL, so the NOT NULL of the 2017 migrations never reached them
COLUMNS = [
    ("posts", "hidden", sa.Boolean(), False),
    ("topics", "hidden", sa.Boolean(), False),
    ("users", "post_count", sa.Integer(), 0),
]


def sqlite_triggers(bind, table_name):
    # batch_alter_table rebuilds the table on SQLite, which drops its triggers
    # (e.g. the full-text search triggers from 1784625534)
    if bind.dialect.name != "sqlite":
        return []
    return (
        bind.exec_driver_sql(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND tbl_name = ?",
            (table_name,),
        )
        .scalars()
        .all()
    )


def restore_triggers(bind, triggers):
    for trigger in triggers:
        bind.exec_driver_sql(trigger)


def upgrade():
    bind = op.get_bind()

    triggers = sqlite_triggers(bind, "users")
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "password",
            existing_type=sa.String(length=120),
            type_=sa.String(length=255),
            existing_nullable=False,
        )
    restore_triggers(bind, triggers)

    # FlaskBB 2.x blocked every plugin that wasn't enabled, NULL included
    plugin_registry = sa.table("plugin_registry", sa.column("enabled", sa.Boolean))
    op.execute(
        plugin_registry.update().where(plugin_registry.c.enabled.is_(None)).values(enabled=False)
    )
    with op.batch_alter_table("plugin_registry") as batch_op:
        batch_op.alter_column("enabled", existing_type=sa.Boolean(), nullable=False)

    inspector = sa.inspect(bind)
    for table_name, column_name, column_type, fill_value in COLUMNS:
        column = next(c for c in inspector.get_columns(table_name) if c["name"] == column_name)
        if not column["nullable"]:
            continue

        table = sa.table(table_name, sa.column(column_name, column_type))
        op.execute(
            table.update().where(table.c[column_name].is_(None)).values({column_name: fill_value})
        )

        triggers = sqlite_triggers(bind, table_name)
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column(column_name, existing_type=column_type, nullable=False)
        restore_triggers(bind, triggers)


def downgrade():
    bind = op.get_bind()

    # installs from 2.2 on already had posts.hidden, topics.hidden and
    # users.post_count non-nullable, so those stay as they are

    with op.batch_alter_table("plugin_registry") as batch_op:
        batch_op.alter_column("enabled", existing_type=sa.Boolean(), nullable=True)

    triggers = sqlite_triggers(bind, "users")
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "password",
            existing_type=sa.String(length=255),
            type_=sa.String(length=120),
            existing_nullable=False,
        )
    restore_triggers(bind, triggers)
