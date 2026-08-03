"""add memberlist_enabled setting

Revision ID: 1785759600
Revises: 1785353838
Create Date: 2026-08-03 14:20:00

"""

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1785759600"
down_revision = "1785353838"
branch_labels = ()
depends_on = None

# must stay in sync with general_group in flaskbb/core/settings/fixture.py
SETTING_KEY = "MEMBERLIST_ENABLED"
SETTING_VALUE = True
GROUP_KEY = "general"

settings_table = sa.table(
    "settings",
    sa.column("key", sa.String),
    sa.column("value", sa.Text),
    sa.column("group_key", sa.String),
)


def upgrade():
    conn = op.get_bind()
    exists = conn.execute(
        sa.select(settings_table.c.key).where(
            settings_table.c.group_key == GROUP_KEY,
            sa.func.lower(settings_table.c.key) == SETTING_KEY.lower(),
        )
    ).first()
    if exists is None:
        conn.execute(
            settings_table.insert().values(
                key=SETTING_KEY,
                value=json.dumps(SETTING_VALUE),
                group_key=GROUP_KEY,
            )
        )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        settings_table.delete().where(
            settings_table.c.group_key == GROUP_KEY,
            sa.func.lower(settings_table.c.key) == SETTING_KEY.lower(),
        )
    )
