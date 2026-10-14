"""add the open_links_in_new_tab and search_snippet_length settings

Both settings were added without a migration, so upgraded installations
had no row for them and their admin settings pages failed.

Revision ID: 1792002242
Revises: 1791490120
Create Date: 2026-10-14 20:24:02

"""

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1792002242"
down_revision = "1791490120"
branch_labels = ()
depends_on = None

# must stay in sync with general_group and misc_group in flaskbb/settings/fixture.py
SETTINGS = (
    ("general", "OPEN_LINKS_IN_NEW_TAB", False),
    ("misc", "SEARCH_SNIPPET_LENGTH", 320),
)

settings_table = sa.table(
    "settings",
    sa.column("key", sa.String),
    sa.column("value", sa.Text),
    sa.column("group_key", sa.String),
)


def _setting(group_key: str, key: str):
    return sa.and_(
        settings_table.c.group_key == group_key,
        sa.func.lower(settings_table.c.key) == key.lower(),
    )


def upgrade():
    conn = op.get_bind()
    for group_key, key, value in SETTINGS:
        exists = conn.execute(
            sa.select(settings_table.c.key).where(_setting(group_key, key))
        ).first()
        if exists is None:
            conn.execute(
                settings_table.insert().values(
                    key=key, value=json.dumps(value), group_key=group_key
                )
            )


def downgrade():
    conn = op.get_bind()
    for group_key, key, _value in SETTINGS:
        conn.execute(settings_table.delete().where(_setting(group_key, key)))
