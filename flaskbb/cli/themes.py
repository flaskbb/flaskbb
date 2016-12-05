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
from flaskbb.cli.utils import check_cookiecutter, validate_theme
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
@click.argument("theme_identifier", callback=check_cookiecutter)
@click.option("--template", "-t", type=click.STRING,
              default="https://github.com/sh4nks/cookiecutter-flaskbb-theme",
              help="Path to a cookiecutter template or to a valid git repo.")
def new_theme(theme_identifier, template):
    """Creates a new theme based on the cookiecutter theme
    template. Defaults to this template:
    https://github.com/sh4nks/cookiecutter-flaskbb-theme.
    It will either accept a valid path on the filesystem
    or a URL to a Git repository which contains the cookiecutter template.
    """
    from cookiecutter.main import cookiecutter
    out_dir = os.path.join(current_app.root_path, "themes")
    click.secho("[+] Creating new theme {}".format(theme_identifier),
                fg="cyan")
    cookiecutter(template, output_dir=out_dir)
    click.secho("[+] Done. Created in {}".format(out_dir),
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
