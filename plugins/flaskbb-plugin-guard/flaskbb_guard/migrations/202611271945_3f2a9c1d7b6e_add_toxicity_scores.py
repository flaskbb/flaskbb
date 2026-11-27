"""Add toxicity_scores table

Revision ID: 3f2a9c1d7b6e
Revises:
Create Date: 2026-11-27 19:45:00

"""

import flaskbb
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3f2a9c1d7b6e"
down_revision = None
branch_labels = ("guard",)
depends_on = "5945d8081a95"


def upgrade():
    con = op.get_bind()
    if not sa.inspect(con).has_table("toxicity_scores"):
        op.create_table(
            "toxicity_scores",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("post_id", sa.Integer(), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("label", sa.String(length=50), nullable=False),
            sa.Column("model_name", sa.String(length=50), nullable=False),
            sa.Column("latency_ms", sa.Float(), nullable=False),
            sa.Column(
                "created",
                flaskbb.utils.database.UTCDateTime(timezone=True),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["post_id"],
                ["posts.id"],
                name=op.f("fk_toxicity_scores_post_id_posts"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_toxicity_scores")),
        )
        op.create_index(
            op.f("ix_toxicity_scores_post_id"), "toxicity_scores", ["post_id"], unique=False
        )


def downgrade():
    op.drop_index(op.f("ix_toxicity_scores_post_id"), table_name="toxicity_scores")
    op.drop_table("toxicity_scores")
