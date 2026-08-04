"""
flaskbb.cli.utils
~~~~~~~~~~~~~~~~~

This module contains some utility helpers that are used across
commands.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import importlib.metadata
import os
import re
import sys
from typing import Any, IO, override

import click
from click._compat import get_text_stderr
from flask_themes2 import get_theme
from jinja2 import Template

from flaskbb import __version__
from flaskbb.extensions import pluggy
from flaskbb.utils.populate import create_user, update_user

_email_regex = r"[^@]+@[^@]+\.[^@]+"


class FlaskBBCLIError(click.ClickException):
    """An exception that signals a usage error including color support.
    This aborts any further handling.

    :param styles: The style kwargs which should be forwarded to click.secho.
    """

    def __init__(self, message: str, **styles: Any):
        click.ClickException.__init__(self, message)
        self.styles = styles

    @override
    def show(self, file: IO[Any] | None = None):
        if file is None:
            file = get_text_stderr()
        click.secho(f"error: {self.format_message()}", file=file, **self.styles)


class EmailType(click.ParamType):
    """The choice type allows a value to be checked against a fixed set of
    supported values.  All of these values have to be strings.
    See :ref:`choice-opts` for an example.
    """

    name = "email"

    @override
    def convert(self, value: str, param: click.Parameter | None, ctx: click.Context | None):
        # Exact match
        if re.match(_email_regex, value):
            return value
        else:
            self.fail((f"invalid email: {value}"), param, ctx)

    @override
    def __repr__(self):
        return "email"


def validate_plugin(plugin: str):
    """Checks if a plugin is installed.
    TODO: Figure out how to use this in a callback. Doesn't work because
          the appcontext can't be found and using with_appcontext doesn't
          help either.
    """
    # list_name holds all plugin names, also the disabled ones (they won't do
    # anything as they are set as 'blocked' on pluggy)
    if plugin not in pluggy.list_name():
        raise FlaskBBCLIError(f"Plugin {plugin} not found.", fg="red")
    return True


def validate_theme(theme: str):
    """Checks if a theme is installed."""
    try:
        get_theme(theme)
    except KeyError as e:
        raise FlaskBBCLIError(f"Theme {theme} not found.", fg="red") from e


def get_cookiecutter() -> object:
    cookiecutter_available = False
    try:
        from cookiecutter.main import cookiecutter  # pyright: ignore

        cookiecutter_available = True
    except ImportError:
        pass

    if not cookiecutter_available:
        raise FlaskBBCLIError(
            "Can't continue because cookiecutter is not installed. "
            + "You can install it with 'pip install cookiecutter'.",
            fg="red",
        )
    return cookiecutter  # pyright: ignore


def get_version(ctx: click.Context, param: str | None, value: str | None) -> None:
    if not value or ctx.resilient_parsing:
        return
    message = "FlaskBB %(version)s using Flask %(flask_version)s on Python %(python_version)s"
    click.echo(
        message
        % {
            "version": __version__,
            "flask_version": importlib.metadata.version("flask"),
            "python_version": sys.version.split("\n")[0],
        },
        color=ctx.color,
    )
    ctx.exit()


def prompt_save_user(
    username: str | None,
    email: str | None,
    password: str | None,
    group: str | None,
):
    if not username:
        username = click.prompt(
            click.style("Username", fg="magenta"),
            type=str,
            default=os.environ.get("USER", ""),
        )
    if not email:
        email = click.prompt(click.style("Email address", fg="magenta"), type=EmailType())
    if not password:
        password = click.prompt(
            click.style("Password", fg="magenta"),
            hide_input=True,
            confirmation_prompt=True,
        )
    if not group:
        group = click.prompt(
            click.style("Group", fg="magenta"),
            type=click.Choice(["admin", "super_mod", "mod", "member"]),
            default="admin",
        )

    return create_user(username, password, email, group)  # pyright: ignore


def prompt_update_user(
    username: str | None,
    email: str | None,
    password: str | None,
    group: str | None,
):
    """Updates a user. Only ``username`` is required; any other option that
    is ``None`` is left unchanged on the user.
    """
    if not username:
        username = click.prompt(
            click.style("Username", fg="magenta"),
            type=str,
            default=os.environ.get("USER", ""),
        )

    return update_user(username, password, email, group)


def prompt_config_path(config_path: str) -> str:
    """Asks for a config path. If the path exists it will ask the user
    for a new path until a he enters a path that doesn't exist.

    :param config_path: The path to the configuration.
    """
    click.secho("The path to save this configuration file.", fg="cyan")
    while True:
        if os.path.exists(config_path) and click.confirm(
            click.style(
                f"Config {config_path} exists. Do you want to overwrite it?",
                fg="magenta",
            )
        ):
            break

        config_path = click.prompt(click.style("Save to", fg="magenta"), default=config_path)

        if not os.path.exists(config_path):
            break

    return config_path


def write_config(config: dict[str, bool | str | int], config_template: Template, config_path: str):
    """Writes a new config file based upon the config template.

    :param config: A dict containing all the key/value pairs which should be
                   used for the new configuration file.
    :param config_template: The config (jinja2-)template.
    :param config_path: The place to write the new config file.
    """
    with open(config_path, "wb") as cfg_file:
        cfg_file.write(config_template.render(**config).encode("utf-8"))
