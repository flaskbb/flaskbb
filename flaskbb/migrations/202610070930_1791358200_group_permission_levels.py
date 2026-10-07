"""replace the granted flag of group_permissions with a level, so a group
can set a permission to never

Revision ID: 1791358200
Revises: 1791294853
Create Date: 2026-10-07 09:30:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1791358200"
down_revision = "1791294853"
branch_labels = ()
depends_on = None


def permissions_table():
    return sa.table(
        "group_permissions",
        sa.column("granted", sa.Boolean),
        sa.column("level", sa.String),
    )


def upgrade():
    bind = op.get_bind()
    permissions = permissions_table()

    op.add_column(
        "group_permissions",
        sa.Column("level", sa.String(length=10), nullable=False, server_default="deny"),
    )
    bind.execute(permissions.update().where(permissions.c.granted.is_(True)).values(level="allow"))
    with op.batch_alter_table("group_permissions") as batch_op:
        batch_op.alter_column("level", server_default=None)
        batch_op.drop_column("granted")


def downgrade():
    bind = op.get_bind()
    permissions = permissions_table()

    op.add_column(
        "group_permissions",
        sa.Column("granted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    bind.execute(permissions.update().where(permissions.c.level == "allow").values(granted=True))
    with op.batch_alter_table("group_permissions") as batch_op:
        batch_op.alter_column("granted", server_default=None)
        batch_op.drop_column("level")
