"""index the columns the forum pages filter, sort and cascade on

Revision ID: 1791490120
Revises: 1791294853
Create Date: 2026-10-08 22:08:40

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1791490120"
down_revision = "1791294853"
branch_labels = ()
depends_on = None

INDEXES = [
    (
        "ix_topics_forum_id_important_last_updated",
        "topics",
        ["forum_id", "important", "last_updated"],
    ),
    ("ix_topics_user_id", "topics", ["user_id"]),
    ("ix_topics_first_post_id", "topics", ["first_post_id"]),
    ("ix_topics_last_post_id", "topics", ["last_post_id"]),
    ("ix_posts_topic_id_id", "posts", ["topic_id", "id"]),
    ("ix_posts_user_id", "posts", ["user_id"]),
    ("ix_topicsread_topic_id", "topicsread", ["topic_id"]),
    ("ix_users_lastseen", "users", ["lastseen"]),
]


def upgrade():
    for name, table, columns in INDEXES:
        op.create_index(name, table, columns, unique=False)


def _mysql_foreign_key_on(table, column):
    """MySQL lets a foreign key use any index on its column and refuses to
    drop the last one, so the key has to go first and come back afterwards."""
    bind = op.get_bind()
    if bind.dialect.name != "mysql":
        return None
    for foreign_key in sa.inspect(bind).get_foreign_keys(table):
        if foreign_key["constrained_columns"] == [column]:
            return foreign_key
    return None


def downgrade():
    for name, table, columns in reversed(INDEXES):
        foreign_key = _mysql_foreign_key_on(table, columns[0])
        if foreign_key:
            op.drop_constraint(foreign_key["name"], table, type_="foreignkey")
        op.drop_index(name, table_name=table)
        if foreign_key:
            op.create_foreign_key(
                foreign_key["name"],
                table,
                foreign_key["referred_table"],
                foreign_key["constrained_columns"],
                foreign_key["referred_columns"],
                **foreign_key["options"],
            )
