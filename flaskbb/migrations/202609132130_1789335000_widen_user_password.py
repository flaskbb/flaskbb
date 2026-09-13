"""widen users.password for scrypt hashes

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


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "password",
            existing_type=sa.String(length=120),
            type_=sa.String(length=255),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "password",
            existing_type=sa.String(length=255),
            type_=sa.String(length=120),
            existing_nullable=False,
        )
