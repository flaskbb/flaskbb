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
from sqlalchemy.exc import IntegrityError

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import (
    EmailType,
    FlaskBBCLIError,
    prompt_save_user,
    prompt_update_user,
)
from flaskbb.extensions import db
from flaskbb.user.models import User


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
def change_user(username, email, password, group):
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
def delete_user(username, force):
    """Deletes an user."""
    if not username:
        username = click.prompt(
            click.style("Username", fg="magenta"),
            type=str,
            default=os.environ.get("USER", ""),
        )

    user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none()
    if user is None:
        raise FlaskBBCLIError(f"The user with username {username} does not exist.", fg="red")

    if not force and not click.confirm(click.style("Are you sure?", fg="magenta")):
        sys.exit(0)

    user.delete()
    click.secho(f"[+] User {user.username} deleted.", fg="cyan")
