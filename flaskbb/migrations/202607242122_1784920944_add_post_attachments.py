"""add post attachments

Revision ID: 1784920944
Revises: 1784625534
Create Date: 2026-07-24 21:22:24

"""

import json

import sqlalchemy as sa
from alembic import op

import flaskbb

# revision identifiers, used by Alembic.
revision = "1784920944"
down_revision = "1784625534"
branch_labels = ()
depends_on = None

# must stay in sync with attachments_group in flaskbb/core/settings/fixture.py
ATTACHMENT_SETTINGS = {
    "ATTACHMENTS_ENABLED": True,
    "ATTACHMENT_IMAGE_PREVIEWS": True,
    "ATTACHMENT_MAX_SIZE": 1024,
    "ATTACHMENTS_PER_POST": 5,
    "ATTACHMENT_TYPES": "png, jpg, jpeg, gif, pdf",
}


def upgrade():
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column(
            "date_created",
            flaskbb.utils.database.UTCDateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_attachments_post_id"), "attachments", ["post_id"], unique=False
    )
    # filename is the lookup key of the download url
    op.create_index(
        op.f("ix_attachments_filename"), "attachments", ["filename"], unique=True
    )

    with op.batch_alter_table("groups", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("postattachment", sa.Boolean(), nullable=True, default=True)
        )

    with op.batch_alter_table("groups", schema=None) as batch_op:
        groups = sa.sql.table(
            "groups",
            sa.sql.column("postattachment"),
            sa.sql.column("postreply"),
        )
        # exactly the groups that may post replies may attach files
        batch_op.execute(
            groups.update()
            .where(groups.c.postreply == True)
            .values(postattachment=True)
        )
        batch_op.execute(
            groups.update()
            .where(groups.c.postreply != True)
            .values(postattachment=False)
        )
        batch_op.alter_column(
            "postattachment", existing_type=sa.Boolean(), nullable=False
        )

    # Seed the attachment settings rows for existing installs
    conn = op.get_bind()
    settings_table = sa.table(
        "settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
        sa.column("group_key", sa.String),
    )
    existing_keys = {
        key.lower()
        for key in conn.execute(
            sa.select(settings_table.c.key).where(
                settings_table.c.group_key == "attachments"
            )
        ).scalars()
    }
    for key, value in ATTACHMENT_SETTINGS.items():
        if key.lower() in existing_keys:
            continue
        conn.execute(
            settings_table.insert().values(
                key=key,
                value=json.dumps(value),
                group_key="attachments",
            )
        )


def downgrade():
    op.execute("DELETE FROM settings WHERE group_key = 'attachments'")

    with op.batch_alter_table("groups", schema=None) as batch_op:
        batch_op.drop_column("postattachment")

    op.drop_index(op.f("ix_attachments_filename"), table_name="attachments")
    op.drop_index(op.f("ix_attachments_post_id"), table_name="attachments")
    op.drop_table("attachments")
