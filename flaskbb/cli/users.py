# -*- coding: utf-8 -*-
"""
    flaskbb.cli.users
    ~~~~~~~~~~~~~~~~~

    This module contains all user commands.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os

import click
from sqlalchemy.exc import IntegrityError

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import FlaskBBCLIError, EmailType, prompt_save_user
from flaskbb.user.models import User


@flaskbb.group()
def users():
    """Create, update or delete users."""
    pass


@users.command("new")
@click.option("--username", "-u", help="The username of the user.")
@click.option("--email", "-e", type=EmailType(),
              help="The email address of the user.")
@click.option("--password", "-p", help="The password of the user.")
@click.option("--group", "-g", help="The group of the user.",
              type=click.Choice(["admin", "super_mod", "mod", "member"]))
def new_user(username, email, password, group):
    """Creates a new user. Omit any options to use the interactive mode."""
    try:
        user = prompt_save_user(username, email, password, group)

        click.secho("[+] User {} with Email {} in Group {} created.".format(
            user.username, user.email, user.primary_group.name), fg="cyan"
        )
    except IntegrityError:
        raise FlaskBBCLIError("Couldn't create the user because the "
                              "username or email address is already taken.",
                              fg="red")


@users.command("update")
@click.option("--username", "-u", help="The username of the user.")
@click.option("--email", "-e", type=EmailType(),
              help="The email address of the user.")
@click.option("--password", "-p", help="The password of the user.")
@click.option("--group", "-g", help="The group of the user.",
              type=click.Choice(["admin", "super_mod", "mod", "member"]))
def change_user(username, email, password, group):
    """Updates an user. Omit any options to use the interactive mode."""

    user = prompt_save_user(username, email, password, group, only_update=True)
    if user is None:
        raise FlaskBBCLIError("The user with username {} does not exist."
                              .format(username), fg="red")

    click.secho("[+] User {} updated.".format(user.username), fg="cyan")


@users.command("delete")
@click.option("--username", "-u", help="The username of the user.")
@click.option("--force", "-f", default=False, is_flag=True,
              help="Removes the user without asking for confirmation.")
def delete_user(username, force):
    """Deletes an user."""
    if not username:
        username = click.prompt(
            click.style("Username", fg="magenta"), type=str,
            default=os.environ.get("USER", "")
        )

    user = User.query.filter_by(username=username).first()
    if user is None:
        raise FlaskBBCLIError("The user with username {} does not exist."
                              .format(username), fg="red")

    if not force and not \
            click.confirm(click.style("Are you sure?", fg="magenta")):
        sys.exit(0)

    user.delete()
    click.secho("[+] User {} deleted.".format(user.username), fg="cyan")
