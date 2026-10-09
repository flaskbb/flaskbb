"""index the columns the forum pages filter, sort and cascade on

Revision ID: 1791490120
Revises: 1791294853
Create Date: 2026-10-08 22:08:40

"""

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


def downgrade():
    for name, table, _columns in reversed(INDEXES):
        op.drop_index(name, table_name=table)
