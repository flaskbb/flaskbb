"""
flaskbb.cli.groups
~~~~~~~~~~~~~~~~~~

This module contains all group commands.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import sys

import click
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import (
    FlaskBBCLIError,
    get_group,
    group_permissions,
    print_details,
    print_table,
)
from flaskbb.extensions import db
from flaskbb.permissions import PermissionLevel
from flaskbb.user.models import Group, GroupRole, User

PROTECTED_GROUP_ID = 6
ROLES = [role.value for role in GroupRole]


def _member_count(group: Group) -> int:
    return User.count(
        sa.or_(
            User.primary_group_id == group.id,
            User.secondary_groups.any(Group.id == group.id),
        )
    )


def _validate_permissions(
    grant: tuple[str, ...], revoke: tuple[str, ...], never: tuple[str, ...] = ()
):
    permissions = group_permissions()
    unknown = set(grant + revoke + never) - set(permissions)
    if unknown:
        raise FlaskBBCLIError(
            "Unknown permission(s): {}. Available permissions: {}.".format(
                ", ".join(sorted(unknown)), ", ".join(permissions)
            ),
            fg="red",
        )

    both = (set(grant) & set(revoke)) | (set(grant) & set(never)) | (set(revoke) & set(never))
    if both:
        raise FlaskBBCLIError(
            "Can't grant and revoke the same permission(s): {}.".format(", ".join(sorted(both))),
            fg="red",
        )


def _update_permissions(
    group: Group, grant: tuple[str, ...], revoke: tuple[str, ...], never: tuple[str, ...] = ()
):
    for permission in grant:
        group.set_permission(permission, PermissionLevel.ALLOW)
    for permission in revoke:
        group.set_permission(permission, PermissionLevel.DENY)
    for permission in never:
        group.set_permission(permission, PermissionLevel.NEVER)


def _validate_role(group: Group, role: GroupRole):
    """The guest and the banned group are looked up by their role, so there
    can only ever be one of each.
    """
    if role not in (GroupRole.GUEST, GroupRole.BANNED):
        return

    existing = db.session.execute(
        sa.select(Group).filter(Group.role == role, Group.id != group.id)
    ).scalar_one_or_none()

    if existing is not None:
        raise FlaskBBCLIError(
            f"Only one group of role '{role.value}' (currently: '{existing.name}') is allowed.",
            fg="red",
        )


@flaskbb.group()
def groups():
    """Create, update or delete groups."""


@groups.command("list")
def list_groups():
    """Lists all groups."""
    all_groups = db.session.execute(sa.select(Group).order_by(Group.id.asc())).scalars()

    rows = [
        [
            str(group.id),
            group.name,
            group.role.value,
            str(_member_count(group)),
            str(group.description or ""),
        ]
        for group in all_groups
    ]

    print_table(["ID", "Name", "Role", "Members", "Description"], rows)


@groups.command("show")
@click.argument("name")
def show_group(name: str):
    """Shows a group including its permissions."""
    group = get_group(name)

    print_details(
        [
            ("ID", str(group.id)),
            ("Name", group.name),
            ("Description", str(group.description or "-")),
            ("Role", group.role.value),
            ("Members", str(_member_count(group))),
        ]
    )

    click.secho("\nPermissions", fg="blue", bold=True)
    for permission, level in group.permission_levels.items():
        marker, color = LEVEL_MARKERS[level]
        click.secho(f"  {marker} {permission}", fg=color)


LEVEL_MARKERS = {
    PermissionLevel.ALLOW: ("[+]", "green"),
    PermissionLevel.DENY: ("[-]", "red"),
    PermissionLevel.NEVER: ("[x]", "red"),
}


@groups.command("new")
@click.argument("name")
@click.option("--description", "-d", help="The description of the group.")
@click.option(
    "--role",
    "-r",
    type=click.Choice(ROLES),
    default=GroupRole.MEMBER.value,
    show_default=True,
    help="The role of the group.",
)
@click.option(
    "--grant",
    multiple=True,
    help="A permission to grant. Can be used multiple times.",
)
@click.option(
    "--revoke",
    multiple=True,
    help="A permission to revoke. Can be used multiple times.",
)
@click.option(
    "--never",
    multiple=True,
    help="A permission to revoke for every member, whatever their other groups allow. "
    "Can be used multiple times.",
)
def new_group(
    name: str,
    description: str | None,
    role: str,
    grant: tuple[str, ...],
    revoke: tuple[str, ...],
    never: tuple[str, ...],
):
    """Creates a new group. Permissions that are neither granted, revoked nor
    set to never keep their default value.
    """
    group = Group(name=name, role=GroupRole(role))
    _validate_permissions(grant, revoke, never)
    _validate_role(group, group.role)

    if description is not None:
        group.description = description
    _update_permissions(group, grant, revoke, never)

    try:
        group.save()
    except IntegrityError as e:
        db.session.rollback()
        raise FlaskBBCLIError(
            f"Couldn't create the group because the name {name} is already taken.",
            fg="red",
        ) from e

    click.secho(f"[+] Group {group.name} created.", fg="cyan")


@groups.command("update")
@click.argument("name")
@click.option("--name", "-n", "new_name", help="The new name of the group.")
@click.option("--description", "-d", help="The description of the group.")
@click.option("--role", "-r", type=click.Choice(ROLES), help="The role of the group.")
@click.option(
    "--grant",
    multiple=True,
    help="A permission to grant. Can be used multiple times.",
)
@click.option(
    "--revoke",
    multiple=True,
    help="A permission to revoke. Can be used multiple times.",
)
@click.option(
    "--never",
    multiple=True,
    help="A permission to revoke for every member, whatever their other groups allow. "
    "Can be used multiple times.",
)
def update_group(
    name: str,
    new_name: str | None,
    description: str | None,
    role: str | None,
    grant: tuple[str, ...],
    revoke: tuple[str, ...],
    never: tuple[str, ...],
):
    """Updates a group. Any option that is omitted is left unchanged."""
    group = get_group(name)

    _validate_permissions(grant, revoke, never)
    if role is not None:
        _validate_role(group, GroupRole(role))
        group.role = GroupRole(role)

    if new_name is not None:
        group.name = new_name
    if description is not None:
        group.description = description
    _update_permissions(group, grant, revoke, never)

    try:
        group.save()
    except IntegrityError as e:
        db.session.rollback()
        raise FlaskBBCLIError(
            f"Couldn't update the group because the name {new_name} is already taken.",
            fg="red",
        ) from e

    click.secho(f"[+] Group {group.name} updated.", fg="cyan")


@groups.command("delete")
@click.argument("name")
@click.option(
    "--force",
    "-f",
    default=False,
    is_flag=True,
    help="Removes the group without asking for confirmation.",
)
def delete_group(name: str, force: bool):
    """Deletes a group. Groups that still have members can't be deleted."""
    group = get_group(name)

    if group.id <= PROTECTED_GROUP_ID:
        raise FlaskBBCLIError(
            f"The standard group {group.name} can't be deleted. Try renaming it instead.",
            fg="red",
        )

    members = _member_count(group)
    if members:
        raise FlaskBBCLIError(
            f"The group {group.name} still has {members} member(s). "
            "Move them to another group first.",
            fg="red",
        )

    if not force and not click.confirm(click.style("Are you sure?", fg="magenta")):
        sys.exit(0)

    group.delete()
    click.secho(f"[+] Group {group.name} deleted.", fg="cyan")
