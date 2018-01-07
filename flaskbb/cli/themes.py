# -*- coding: utf-8 -*-
"""
    flaskbb.cli.themes
    ~~~~~~~~~~~~~~~~~~

    This module contains all theme commands.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
import shutil

import click
from flask import current_app
from flask_themes2 import get_themes_list, get_theme

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import get_cookiecutter, validate_theme
from flaskbb.utils.settings import flaskbb_config


@flaskbb.group()
def themes():
    """Themes command sub group."""
    pass


@themes.command("list")
def list_themes():
    """Lists all installed themes."""
    click.secho("[+] Listing all installed themes...", fg="cyan")

    active_theme = get_theme(flaskbb_config['DEFAULT_THEME'])
    available_themes = set(get_themes_list()) - set([active_theme])

    click.secho("[+] Active Theme:", fg="blue", bold=True)
    click.secho("    - {} (version {})".format(
        active_theme.name, active_theme.version), bold=True
    )

    click.secho("[+] Available Themes:", fg="yellow", bold=True)
    for theme in available_themes:
        click.secho("    - {} (version {})".format(
            theme.name, theme.version), bold=True
        )


@themes.command("new")
@click.option("--template", "-t", type=click.STRING,
              default="https://github.com/sh4nks/cookiecutter-flaskbb-theme",
              help="Path to a cookiecutter template or to a valid git repo.")
@click.option("--out-dir", "-o", type=click.Path(), default=None,
              help="The location for the new FlaskBB theme.")
@click.option("--force", "-f", is_flag=True, default=False,
              help="Overwrite the contents of output directory if it exists")
def new_theme(template, out_dir, force):
    """Creates a new theme based on the cookiecutter theme
    template. Defaults to this template:
    https://github.com/sh4nks/cookiecutter-flaskbb-theme.
    It will either accept a valid path on the filesystem
    or a URL to a Git repository which contains the cookiecutter template.
    """
    cookiecutter = get_cookiecutter()

    if out_dir is None:
        out_dir = click.prompt(
            "Saving theme in",
            default=os.path.join(current_app.root_path, "themes")
        )

    r = cookiecutter(template, output_dir=out_dir, overwrite_if_exists=force)
    click.secho("[+] Created new theme in {}".format(r),
                fg="green", bold=True)


@themes.command("remove")
@click.argument("theme_identifier")
@click.option("--force", "-f", default=False, is_flag=True,
              help="Removes the theme without asking for confirmation.")
def remove_theme(theme_identifier, force):
    """Removes a theme from the filesystem."""
    validate_theme(theme_identifier)
    if not force and not \
            click.confirm(click.style("Are you sure?", fg="magenta")):
        sys.exit(0)

    theme = get_theme(theme_identifier)
    click.secho("[+] Removing theme from filesystem...", fg="cyan")
    shutil.rmtree(theme.path, ignore_errors=False, onerror=None)
