"""add open_links_in_new_tab to users

Revision ID: 1785353838
Revises: 1784920944
Create Date: 2026-07-29 21:37:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1785353838"
down_revision = "1784920944"
branch_labels = ()
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("open_links_in_new_tab", sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("open_links_in_new_tab")
