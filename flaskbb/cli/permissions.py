"""
flaskbb.cli.permissions
~~~~~~~~~~~~~~~~~~~~~~~

This module contains all permission commands.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import click
import sqlalchemy as sa

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import (
    FlaskBBCLIError,
    get_group,
    get_user,
    group_permissions,
    print_table,
)
from flaskbb.extensions import db
from flaskbb.permissions import PermissionLevel
from flaskbb.user.models import Group, permissions_of


def _validate_permission(permission: str):
    available = group_permissions()
    if permission not in available:
        raise FlaskBBCLIError(
            f"Unknown permission: {permission}. Available permissions: {', '.join(available)}.",
            fg="red",
        )


@flaskbb.group()
def permissions():
    """Show or modify the permissions of the groups."""


@permissions.command("list")
@click.option("--group", "-g", "group_name", help="Only show the permissions of this group.")
def list_permissions(group_name: str | None):
    """Lists the permissions of every group."""
    if group_name:
        selected = [get_group(group_name)]
    else:
        selected = list(db.session.execute(sa.select(Group).order_by(Group.id.asc())).scalars())

    rows = [
        [permission] + [group.permission_levels[permission].value for group in selected]
        for permission in group_permissions()
    ]

    print_table(["Permission"] + [group.name for group in selected], rows)


@permissions.command("show")
@click.argument("username")
def show_permissions(username: str):
    """Shows the effective permissions of a user."""
    user = get_user(username)
    user_groups = [user.primary_group] + list(user.secondary_groups)

    click.secho(f"[+] Permissions of {user.username}", fg="blue", bold=True)
    click.secho("Groups: {}".format(", ".join(group.name for group in user_groups)))

    effective = permissions_of(user_groups)
    rows: list[list[str]] = []
    for permission in group_permissions():
        levels = {group.name: group.permission_levels[permission] for group in user_groups}
        never_by = [name for name, level in levels.items() if level is PermissionLevel.NEVER]
        granted_by = [name for name, level in levels.items() if level is PermissionLevel.ALLOW]
        decided_by = never_by if never_by else granted_by
        rows.append(
            [
                permission,
                "never" if never_by else "yes" if effective[permission] else "no",
                ", ".join(decided_by) if decided_by else "-",
            ]
        )

    print_table(["Permission", "Granted", "Granted by"], rows)


LEVEL_ALIASES = {"true": PermissionLevel.ALLOW, "false": PermissionLevel.DENY}


@permissions.command("set")
@click.argument("group_name", metavar="GROUP")
@click.argument("permission")
@click.argument(
    "value",
    type=click.Choice([*PermissionLevel, *LEVEL_ALIASES], case_sensitive=False),
)
def set_permission(group_name: str, permission: str, value: str):
    """Sets a single permission of a group.

    VALUE is 'allow', 'deny' or 'never'; 'true' and 'false' stand for allow
    and deny. A member has a permission when any of their groups allows it,
    unless one of their groups has set it to never.
    """
    _validate_permission(permission)
    group = get_group(group_name)
    level = LEVEL_ALIASES[value] if value in LEVEL_ALIASES else PermissionLevel(value)

    group.set_permission(permission, level)
    group.save()

    click.secho(
        f"[+] Permission {permission} of group {group.name} set to {level.value}.",
        fg="cyan",
    )
