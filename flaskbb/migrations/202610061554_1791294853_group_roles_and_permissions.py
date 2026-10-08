"""replace the group type flags with a role and the permission columns with
group_permissions rows, whose level lets a group set a permission to never

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
        sa.column("level", sa.String),
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
        sa.Column("level", sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint("group_id", "permission"),
    )
    op.add_column(
        "groups",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),
    )

    groups = groups_table()
    permissions = permissions_table()
    for row in bind.execute(sa.select(groups)).mappings().all():
        role = next((flag for flag in ROLE_FLAGS if row[flag]), "member")
        bind.execute(groups.update().where(groups.c.id == row["id"]).values(role=role))
        bind.execute(
            permissions.insert(),
            [
                {
                    "group_id": row["id"],
                    "permission": name,
                    "level": "allow" if row[name] else "deny",
                }
                for name in PERMISSIONS
            ],
        )

    if needs_rebuild(bind):
        with op.batch_alter_table("groups") as batch_op:
            for name in ROLE_FLAGS + PERMISSIONS:
                batch_op.drop_column(name)
    else:
        for name in ROLE_FLAGS + PERMISSIONS:
            op.drop_column("groups", name)


def needs_rebuild(bind):
    """SQLite drops a column in place since 3.35, unless a constraint refers
    to it: FlaskBB 2.x created a CHECK constraint per boolean column there,
    and only rebuilding the table gets rid of those along with the columns.
    """
    if bind.dialect.name != "sqlite":
        return False
    if bind.dialect.server_version_info < (3, 35):
        return True
    return bool(sa.inspect(bind).get_check_constraints("groups"))


def downgrade():
    bind = op.get_bind()

    for name in ROLE_FLAGS + PERMISSIONS:
        op.add_column(
            "groups", sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.false())
        )

    groups = groups_table()
    permissions = permissions_table()
    for group_id, role in bind.execute(sa.select(groups.c.id, groups.c.role)).all():
        values = {flag: flag == role for flag in ROLE_FLAGS}
        levels = bind.execute(
            sa.select(permissions.c.permission, permissions.c.level).where(
                permissions.c.group_id == group_id
            )
        ).all()
        values.update({name: level == "allow" for name, level in levels if name in PERMISSIONS})
        bind.execute(groups.update().where(groups.c.id == group_id).values(**values))

    op.drop_column("groups", "role")
    op.drop_table("group_permissions")
