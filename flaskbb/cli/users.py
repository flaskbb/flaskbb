"""
flaskbb.cli.users
~~~~~~~~~~~~~~~~~

This module contains all user commands.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import os
import sys

import click
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import (
    EmailType,
    FlaskBBCLIError,
    get_group,
    get_user,
    group_permissions,
    print_details,
    print_table,
    prompt_save_user,
    prompt_update_user,
)
from flaskbb.extensions import db
from flaskbb.user.models import Group, User


@flaskbb.group()
def users():
    """Create, update or delete users."""
    pass


@users.command("new")
@click.option("--username", "-u", help="The username of the user.")
@click.option("--email", "-e", type=EmailType(), help="The email address of the user.")
@click.option("--password", "-p", help="The password of the user.")
@click.option(
    "--group",
    "-g",
    help="The group of the user.",
    type=click.Choice(["admin", "super_mod", "mod", "member"]),
)
def new_user(username: str | None, email: str | None, password: str | None, group: str | None):
    """Creates a new user. Omit any options to use the interactive mode."""
    try:
        user = prompt_save_user(username, email, password, group)

        click.secho(
            f"[+] User {user.username} with Email {user.email} in Group {user.primary_group.name} created.",  # noqa: E501
            fg="cyan",
        )
    except IntegrityError as e:
        raise FlaskBBCLIError(
            "Couldn't create the user because the username or email address is already taken.",
            fg="red",
        ) from e


@users.command("update")
@click.option("--username", "-u", help="The username of the user.")
@click.option("--email", "-e", type=EmailType(), help="The email address of the user.")
@click.option("--password", "-p", help="The password of the user.")
@click.option(
    "--group",
    "-g",
    help="The group of the user.",
    type=click.Choice(["admin", "super_mod", "mod", "member"]),
)
def change_user(username: str | None, email: str | None, password: str | None, group: str | None):
    """Updates an user. Only the username is required; any other option
    that is omitted is left unchanged."""

    user = prompt_update_user(username, email, password, group)
    if user is None:
        raise FlaskBBCLIError(f"The user with username {username} does not exist.", fg="red")

    click.secho(f"[+] User {user.username} updated.", fg="cyan")


@users.command("delete")
@click.option("--username", "-u", help="The username of the user.")
@click.option(
    "--force",
    "-f",
    default=False,
    is_flag=True,
    help="Removes the user without asking for confirmation.",
)
def delete_user(username: str | None, force: bool):
    """Deletes an user."""
    if not username:
        username = click.prompt(
            click.style("Username", fg="magenta"),
            type=str,
            default=os.environ.get("USER", ""),
        )

    user = db.session.execute(sa.select(User).filter_by(username=username)).scalar_one_or_none()
    if user is None:
        raise FlaskBBCLIError(f"The user with username {username} does not exist.", fg="red")

    if not force and not click.confirm(click.style("Are you sure?", fg="magenta")):
        sys.exit(0)

    user.delete()
    click.secho(f"[+] User {user.username} deleted.", fg="cyan")


@users.command("list")
@click.option("--group", "-g", "group_name", help="Only show users who are in this group.")
@click.option("--banned", "-b", default=False, is_flag=True, help="Only show banned users.")
@click.option(
    "--unactivated",
    "-U",
    default=False,
    is_flag=True,
    help="Only show users who haven't activated their account yet.",
)
def list_users(group_name: str | None, banned: bool, unactivated: bool):
    """Lists all users."""
    stmt = sa.select(User).order_by(User.id.asc())

    if group_name:
        group = get_group(group_name)
        stmt = stmt.filter(
            sa.or_(
                User.primary_group_id == group.id,
                User.secondary_groups.any(Group.id == group.id),
            )
        )
    if banned:
        stmt = stmt.filter(User.primary_group.has(Group.banned.is_(True)))
    if unactivated:
        stmt = stmt.filter(User.activated.is_(False))

    rows = [
        [
            str(user.id),
            user.username,
            user.email,
            user.primary_group.name,
            "yes" if user.activated else "no",
            str(user.post_count),
            user.date_joined.strftime("%Y-%m-%d"),
        ]
        for user in db.session.execute(stmt).scalars()
    ]

    if not rows:
        click.secho("[+] No users found.", fg="yellow")
        return

    print_table(["ID", "Username", "Email", "Group", "Activated", "Posts", "Joined"], rows)


@users.command("show")
@click.argument("username")
def show_user(username: str):
    """Shows a user including his groups and permissions."""
    user = get_user(username)
    secondary_groups = list(user.secondary_groups)

    print_details(
        [
            ("ID", str(user.id)),
            ("Username", user.username),
            ("Email", user.email),
            ("Primary group", user.primary_group.name),
            (
                "Secondary groups",
                ", ".join(group.name for group in secondary_groups) if secondary_groups else "-",
            ),
            ("Activated", "yes" if user.activated else "no"),
            ("Posts", str(user.post_count)),
            ("Joined", user.date_joined.strftime("%Y-%m-%d %H:%M")),
            ("Last seen", user.lastseen.strftime("%Y-%m-%d %H:%M") if user.lastseen else "-"),
        ]
    )

    granted = [
        permission
        for permission in group_permissions()
        if any(getattr(group, permission) for group in [user.primary_group] + secondary_groups)
    ]
    click.secho("\nPermissions", fg="blue", bold=True)
    click.echo("  {}".format(", ".join(granted) if granted else "-"))


@users.command("ban")
@click.argument("username")
def ban_user(username: str):
    """Bans a user by moving him into the banned group."""
    user = get_user(username)

    if not user.ban():
        raise FlaskBBCLIError(f"The user {user.username} is already banned.", fg="red")

    click.secho(f"[+] User {user.username} banned.", fg="cyan")


@users.command("unban")
@click.argument("username")
def unban_user(username: str):
    """Unbans a user by moving him back into the member group."""
    user = get_user(username)

    if not user.unban():
        raise FlaskBBCLIError(f"The user {user.username} is not banned.", fg="red")

    click.secho(f"[+] User {user.username} unbanned.", fg="cyan")


@users.command("activate")
@click.argument("username")
def activate_user(username: str):
    """Activates a user's account."""
    user = get_user(username)

    if user.activated:
        raise FlaskBBCLIError(f"The user {user.username} is already activated.", fg="red")

    user.activated = True
    user.save()
    click.secho(f"[+] User {user.username} activated.", fg="cyan")


@users.command("deactivate")
@click.argument("username")
def deactivate_user(username: str):
    """Deactivates a user's account."""
    user = get_user(username)

    if not user.activated:
        raise FlaskBBCLIError(f"The user {user.username} is already deactivated.", fg="red")

    user.activated = False
    user.save()
    click.secho(f"[+] User {user.username} deactivated.", fg="cyan")


@users.command("set-group")
@click.argument("username")
@click.argument("group_name", metavar="GROUP")
def set_primary_group(username: str, group_name: str):
    """Sets the primary group of a user."""
    user = get_user(username)
    group = get_group(group_name)

    if user.primary_group_id == group.id:
        raise FlaskBBCLIError(
            f"{group.name} already is the primary group of {user.username}.", fg="red"
        )

    # a group is either the primary or a secondary group, never both
    user.remove_from_group(group)
    user.primary_group_id = group.id
    user.save()
    user.invalidate_cache()

    click.secho(f"[+] Primary group of {user.username} set to {group.name}.", fg="cyan")


@users.command("add-group")
@click.argument("username")
@click.argument("group_name", metavar="GROUP")
def add_to_group(username: str, group_name: str):
    """Adds a user to a secondary group."""
    user = get_user(username)
    group = get_group(group_name)

    if user.primary_group_id == group.id:
        raise FlaskBBCLIError(
            f"{group.name} already is the primary group of {user.username}.", fg="red"
        )
    if user.in_group(group):
        raise FlaskBBCLIError(f"{user.username} already is in the group {group.name}.", fg="red")

    user.add_to_group(group)
    user.save()
    user.invalidate_cache()

    click.secho(f"[+] User {user.username} added to group {group.name}.", fg="cyan")


@users.command("remove-group")
@click.argument("username")
@click.argument("group_name", metavar="GROUP")
def remove_from_group(username: str, group_name: str):
    """Removes a user from a secondary group."""
    user = get_user(username)
    group = get_group(group_name)

    if not user.in_group(group):
        raise FlaskBBCLIError(f"{user.username} is not in the group {group.name}.", fg="red")

    user.remove_from_group(group)
    user.save()
    user.invalidate_cache()

    click.secho(f"[+] User {user.username} removed from group {group.name}.", fg="cyan")
