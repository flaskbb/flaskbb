"""replace the group type flags with a role and the permission columns with
group_permissions rows

Revision ID: 1791294853
Revises: 1789335000
Create Date: 2026-10-06 15:54:13

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1791294853"
down_revision = "1789335000"
branch_labels = ()
depends_on = None

ROLE_FLAGS = ["admin", "super_mod", "mod", "banned", "guest"]
PERMISSIONS = [
    "editpost",
    "deletepost",
    "deletetopic",
    "posttopic",
    "postreply",
    "postattachment",
    "mod_edituser",
    "mod_banuser",
    "viewhidden",
    "makehidden",
]


def groups_table():
    return sa.table(
        "groups",
        sa.column("id", sa.Integer),
        sa.column("role", sa.String),
        *[sa.column(name, sa.Boolean) for name in ROLE_FLAGS + PERMISSIONS],
    )


def permissions_table():
    return sa.table(
        "group_permissions",
        sa.column("group_id", sa.Integer),
        sa.column("permission", sa.String),
        sa.column("granted", sa.Boolean),
    )


def upgrade():
    bind = op.get_bind()

    op.create_table(
        "group_permissions",
        sa.Column(
            "group_id",
            sa.Integer(),
            sa.ForeignKey("groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("permission", sa.String(length=255), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("group_id", "permission"),
    )
    op.add_column("groups", sa.Column("role", sa.String(length=20), nullable=True))

    groups = groups_table()
    permissions = permissions_table()
    for row in bind.execute(sa.select(groups)).mappings().all():
        role = next((flag for flag in ROLE_FLAGS if row[flag]), "member")
        bind.execute(groups.update().where(groups.c.id == row["id"]).values(role=role))
        bind.execute(
            permissions.insert(),
            [
                {"group_id": row["id"], "permission": name, "granted": bool(row[name])}
                for name in PERMISSIONS
            ],
        )

    with op.batch_alter_table("groups") as batch_op:
        batch_op.alter_column("role", existing_type=sa.String(length=20), nullable=False)
        for name in ROLE_FLAGS + PERMISSIONS:
            batch_op.drop_column(name)


def downgrade():
    bind = op.get_bind()

    with op.batch_alter_table("groups") as batch_op:
        for name in ROLE_FLAGS + PERMISSIONS:
            batch_op.add_column(
                sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.false())
            )

    groups = groups_table()
    permissions = permissions_table()
    for group_id, role in bind.execute(sa.select(groups.c.id, groups.c.role)).all():
        values = {flag: flag == role for flag in ROLE_FLAGS}
        granted = bind.execute(
            sa.select(permissions.c.permission, permissions.c.granted).where(
                permissions.c.group_id == group_id
            )
        ).all()
        values.update({name: bool(value) for name, value in granted if name in PERMISSIONS})
        bind.execute(groups.update().where(groups.c.id == group_id).values(**values))

    with op.batch_alter_table("groups") as batch_op:
        batch_op.drop_column("role")
    op.drop_table("group_permissions")
