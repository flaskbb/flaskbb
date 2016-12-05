# -*- coding: utf-8 -*-
"""
    flaskbb.cli.utils
    ~~~~~~~~~~~~~~~~~

    This module contains some utility helpers that are used across
    commands.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
import re


import click

from flask import __version__ as flask_version
from flask_themes2 import get_theme

from flaskbb import __version__
from flaskbb.extensions import plugin_manager
from flaskbb.utils.populate import create_user, update_user


cookiecutter_available = False
try:
    from cookiecutter.main import cookiecutter
    cookiecutter_available = True
except ImportError:
    pass

_email_regex = r"[^@]+@[^@]+\.[^@]+"


class FlaskBBCLIError(click.ClickException):
    """An exception that signals a usage error including color support.
    This aborts any further handling.

    :param styles: The style kwargs which should be forwarded to click.secho.
    """

    def __init__(self, message, **styles):
        click.ClickException.__init__(self, message)
        self.styles = styles

    def show(self, file=None):
        if file is None:
            file = click._compat.get_text_stderr()
        click.secho("[-] Error: %s" % self.format_message(), file=file,
                    **self.styles)


class EmailType(click.ParamType):
    """The choice type allows a value to be checked against a fixed set of
    supported values.  All of these values have to be strings.
    See :ref:`choice-opts` for an example.
    """
    name = "email"

    def convert(self, value, param, ctx):
        # Exact match
        if re.match(_email_regex, value):
            return value
        else:
            self.fail(("invalid email: %s" % value), param, ctx)

    def __repr__(self):
        return "email"


def save_user_prompt(username, email, password, group, only_update=False):
    if not username:
        username = click.prompt(
            click.style("Username", fg="magenta"), type=str,
            default=os.environ.get("USER", "")
        )
    if not email:
        email = click.prompt(
            click.style("Email address", fg="magenta"), type=EmailType()
        )
    if not password:
        password = click.prompt(
            click.style("Password", fg="magenta"), hide_input=True,
            confirmation_prompt=True
        )
    if not group:
        group = click.prompt(
            click.style("Group", fg="magenta"),
            type=click.Choice(["admin", "super_mod", "mod", "member"]),
            default="admin"
        )

    if only_update:
        return update_user(username, password, email, group)
    return create_user(username, password, email, group)


def validate_plugin(plugin):
    """Checks if a plugin is installed.
    TODO: Figure out how to use this in a callback. Doesn't work because
          the appcontext can't be found and using with_appcontext doesn't
          help either.
    """
    if plugin not in plugin_manager.all_plugins.keys():
        raise FlaskBBCLIError("Plugin {} not found.".format(plugin), fg="red")
    return True


def validate_theme(theme):
    """Checks if a theme is installed."""
    try:
        get_theme(theme)
    except KeyError:
        raise FlaskBBCLIError("Theme {} not found.".format(theme), fg="red")


def check_cookiecutter(ctx, param, value):
    if not cookiecutter_available:
        raise FlaskBBCLIError(
            "Can't create {} because cookiecutter is not installed. "
            "You can install it with 'pip install cookiecutter'.".
            format(value), fg="red"
        )
    return value


def get_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    message = ("FlaskBB %(version)s using Flask %(flask_version)s on "
               "Python %(python_version)s")
    click.echo(message % {
        'version': __version__,
        'flask_version': flask_version,
        'python_version': sys.version.split("\n")[0]
    }, color=ctx.color)
    ctx.exit()
