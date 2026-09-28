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
    GROUP_TYPES,
    invalidate_permission_cache,
    print_details,
    print_table,
)
from flaskbb.extensions import db
from flaskbb.user.models import Group, User

PROTECTED_GROUP_ID = 6


def _group_type(group: Group) -> str:
    for group_type in GROUP_TYPES:
        if getattr(group, group_type):
            return group_type
    return "member"


def _member_count(group: Group) -> int:
    return User.count(
        sa.or_(
            User.primary_group_id == group.id,
            User.secondary_groups.any(Group.id == group.id),
        )
    )


def _validate_permissions(grant: tuple[str, ...], revoke: tuple[str, ...]):
    permissions = group_permissions()
    unknown = set(grant + revoke) - set(permissions)
    if unknown:
        raise FlaskBBCLIError(
            "Unknown permission(s): {}. Available permissions: {}.".format(
                ", ".join(sorted(unknown)), ", ".join(permissions)
            ),
            fg="red",
        )

    both = set(grant) & set(revoke)
    if both:
        raise FlaskBBCLIError(
            "Can't grant and revoke the same permission(s): {}.".format(", ".join(sorted(both))),
            fg="red",
        )


def _update_permissions(group: Group, grant: tuple[str, ...], revoke: tuple[str, ...]):
    for permission in grant:
        setattr(group, permission, True)
    for permission in revoke:
        setattr(group, permission, False)


def _update_group_type(group: Group, group_type: str):
    for candidate in GROUP_TYPES:
        setattr(group, candidate, candidate == group_type)


def _validate_group_type(group: Group, group_type: str):
    """The guest and the banned group are looked up by their type, so there
    can only ever be one of each.
    """
    if group_type not in ("guest", "banned"):
        return

    existing = db.session.execute(
        sa.select(Group).filter(
            getattr(Group, group_type).is_(True),
            Group.id != group.id,
        )
    ).scalar_one_or_none()

    if existing is not None:
        raise FlaskBBCLIError(
            f"Only one group of type '{group_type}' (currently: '{existing.name}') is allowed.",
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
            _group_type(group),
            str(_member_count(group)),
            str(group.description or ""),
        ]
        for group in all_groups
    ]

    print_table(["ID", "Name", "Type", "Members", "Description"], rows)


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
            ("Type", _group_type(group)),
            ("Members", str(_member_count(group))),
        ]
    )

    click.secho("\nPermissions", fg="blue", bold=True)
    for permission in group_permissions():
        granted = getattr(group, permission)
        click.secho(
            f"  {'[+]' if granted else '[-]'} {permission}",
            fg="green" if granted else "red",
        )


@groups.command("new")
@click.argument("name")
@click.option("--description", "-d", help="The description of the group.")
@click.option(
    "--type",
    "-t",
    "group_type",
    type=click.Choice(GROUP_TYPES),
    help="The type of the group. Omit it to create an ordinary member group.",
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
def new_group(
    name: str,
    description: str | None,
    group_type: str | None,
    grant: tuple[str, ...],
    revoke: tuple[str, ...],
):
    """Creates a new group. Permissions that are neither granted nor revoked
    are set to their default value.
    """
    group = Group(name=name)
    _validate_permissions(grant, revoke)
    if group_type is not None:
        _validate_group_type(group, group_type)
        _update_group_type(group, group_type)

    if description is not None:
        group.description = description
    _update_permissions(group, grant, revoke)

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
@click.option(
    "--type",
    "-t",
    "group_type",
    type=click.Choice([*GROUP_TYPES, "member"]),
    help="The type of the group. Use 'member' to turn it into an ordinary group.",
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
def update_group(
    name: str,
    new_name: str | None,
    description: str | None,
    group_type: str | None,
    grant: tuple[str, ...],
    revoke: tuple[str, ...],
):
    """Updates a group. Any option that is omitted is left unchanged."""
    group = get_group(name)

    _validate_permissions(grant, revoke)
    if group_type is not None:
        _validate_group_type(group, group_type)
        _update_group_type(group, group_type)

    if new_name is not None:
        group.name = new_name
    if description is not None:
        group.description = description
    _update_permissions(group, grant, revoke)

    try:
        group.save()
    except IntegrityError as e:
        db.session.rollback()
        raise FlaskBBCLIError(
            f"Couldn't update the group because the name {new_name} is already taken.",
            fg="red",
        ) from e

    invalidate_permission_cache(group)
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
