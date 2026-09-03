"""
flaskbb.cli.permissions
~~~~~~~~~~~~~~~~~~~~~~~

This module contains all permission commands.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import click

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import (
    FlaskBBCLIError,
    get_group,
    get_user,
    group_permissions,
    invalidate_permission_cache,
    print_table,
)
from flaskbb.extensions import db
from flaskbb.user.models import Group


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
        selected = list(db.session.execute(db.select(Group).order_by(Group.id.asc())).scalars())

    rows = [
        [permission] + ["yes" if getattr(group, permission) else "no" for group in selected]
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

    rows: list[list[str]] = []
    for permission in group_permissions():
        granted_by = [group.name for group in user_groups if getattr(group, permission)]
        rows.append(
            [
                permission,
                "yes" if granted_by else "no",
                ", ".join(granted_by) if granted_by else "-",
            ]
        )

    print_table(["Permission", "Granted", "Granted by"], rows)


@permissions.command("set")
@click.argument("group_name", metavar="GROUP")
@click.argument("permission")
@click.argument("value", type=click.BOOL)
def set_permission(group_name: str, permission: str, value: bool):
    """Grants or revokes a single permission of a group.

    VALUE is a boolean, e.g. 'true' or 'false'.
    """
    _validate_permission(permission)
    group = get_group(group_name)

    setattr(group, permission, value)
    group.save()
    invalidate_permission_cache(group)

    click.secho(
        f"[+] Permission {permission} of group {group.name} set to {str(value).lower()}.",
        fg="cyan",
    )
