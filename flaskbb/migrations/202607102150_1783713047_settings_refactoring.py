"""settings refactoring

Revision ID: 1783713047
Revises: 5945d8081a95
Create Date: 2026-07-10 21:50:47.124127

"""

import json
import pickle

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1783713047"
down_revision = "5945d8081a95"
branch_labels = ()
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Add a temporary column to hold the new JSON text
    op.add_column("settings", sa.Column("value_json", sa.Text(), nullable=True))

    # Add the group_key column
    op.add_column(
        "settings", sa.Column("group_key", sa.String(length=255), nullable=True)
    )
    op.create_index("ix_settings_group_key", "settings", ["group_key"], unique=False)

    # 2. Read every row, unpickle the old value, dump it as JSON
    settings_table = sa.table(
        "settings",
        sa.column("key", sa.String),
        sa.column("settingsgroup", sa.String),
        sa.column("value", sa.LargeBinary),
        sa.column("value_json", sa.Text),
        sa.column("group_key", sa.String),
    )
    rows = conn.execute(
        sa.select(
            settings_table.c.key, settings_table.c.value, settings_table.c.settingsgroup
        )
    ).fetchall()
    for key, raw_value, group_key in rows:
        print(group_key, key, raw_value)
        try:
            python_value = pickle.loads(raw_value)
        except Exception as e:
            raise RuntimeError(f"Could not unpickle setting '{key}': {e}")
        conn.execute(
            settings_table.update()
            .where(settings_table.c.key == key)
            .values(value_json=json.dumps(python_value), group_key=group_key)
        )

    with op.batch_alter_table("settings", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_settings_settingsgroup_settingsgroup"), type_="foreignkey"
        )
        batch_op.alter_column("group_key", existing_type=sa.String, nullable=False)
        batch_op.drop_column("description")
        batch_op.drop_column("extra")
        batch_op.drop_column("value_type")
        batch_op.drop_column("name")
        batch_op.drop_column("settingsgroup")
        batch_op.drop_column("value")
        batch_op.alter_column("value_json", new_column_name="value")

    op.drop_table("settingsgroup")


def downgrade():
    conn = op.get_bind()
    op.add_column(
        "settings", sa.Column("value_pickle", sa.LargeBinary(), nullable=True)
    )

    settings_table = sa.table(
        "settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
        sa.column("value_pickle", sa.LargeBinary),
    )
    rows = conn.execute(
        sa.select(settings_table.c.key, settings_table.c.value)
    ).fetchall()
    for key, json_value in rows:
        python_value = json.loads(json_value)
        conn.execute(
            settings_table.update()
            .where(settings_table.c.key == key)
            .values(value_pickle=pickle.dumps(python_value))
        )

    op.drop_column("settings", "value")
    op.alter_column("settings", "value_pickle", new_column_name="value")
