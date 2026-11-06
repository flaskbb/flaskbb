"""store the reCAPTCHA keys in the settings table again

FlaskBB 2.2 moved the keys to the config file. Installations upgraded
from 2.x still have their rows, so only the missing ones are added.

Revision ID: 1793999700
Revises: 1793996619
Create Date: 2026-11-06 22:15:00

"""

import json

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1793999700"
down_revision = "1793996619"
branch_labels = ()
depends_on = None

# must stay in sync with auth_group in flaskbb/settings/fixture.py
SETTINGS = (
    ("auth", "RECAPTCHA_PUBLIC_KEY", ""),
    ("auth", "RECAPTCHA_PRIVATE_KEY", ""),
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
