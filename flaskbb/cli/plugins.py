# -*- coding: utf-8 -*-
"""
    flaskbb.cli.plugins
    ~~~~~~~~~~~~~~~~~~~

    This module contains all plugin commands.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
import shutil

import click
from flask import current_app
from flask_plugins import (get_all_plugins, get_enabled_plugins,
                           get_plugin_from_all)

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import check_cookiecutter, validate_plugin
from flaskbb.extensions import plugin_manager

try:
    from cookiecutter.main import cookiecutter
except ImportError:
    pass


@flaskbb.group()
def plugins():
    """Plugins command sub group."""
    pass


@plugins.command("new")
@click.option("--full_name", help="Your Name")
@click.option("--email", help="Your email address (eq. you@example.com)")
@click.option("--plugin_name", help="Plugin Name")
@click.option("--plugin_identifier", help="Identifier for the plugin eg plugin_name")
@click.option("--plugin_classname", help="Plugin class name eg PluginName")
@click.option("--description", help="A description of the plugin")
@click.option("--website", help="Website address")
@click.option("--version", help="Version name")
@click.option("--template", "-t", type=click.STRING,
              default="https://github.com/sh4nks/cookiecutter-flaskbb-plugin",
              help="Path to a cookiecutter template or to a valid git repo.")
def new_plugin(template, **cookie_context):
    """Creates a new plugin based on the cookiecutter plugin
    template. Defaults to this template:
    https://github.com/sh4nks/cookiecutter-flaskbb-plugin.
    It will either accept a valid path on the filesystem
    or a URL to a Git repository which contains the cookiecutter template.
    """
    check_cookiecutter(None,None,'plugin')
    out_dir = os.path.join(current_app.root_path, "plugins")
    cookie_context = {k: v for k, v in cookie_context.items() if v}
    if cookie_context.get('plugin_name'):
        cookie_context.setdefault('plugin_identifier', cookie_context['plugin_name'].lower().replace(' ', ''))
        cookie_context.setdefault('plugin_classname', cookie_context['plugin_name'].title().replace(' ', ''))

    click.secho("[+] Creating new plugin...",
                fg="cyan")
    try:
        newdir=cookiecutter(template, output_dir=out_dir,extra_context=cookie_context)
        click.secho("[+] Done. Created in {}".format(newdir),
                fg="green", bold=True)
    except Exception as e:
        click.secho("[-] Couldn't create plugin because of following "
                    "exception: \n{}".format(e), fg="red")


@plugins.command("install")
@click.argument("plugin_identifier")
def install_plugin(plugin_identifier):
    """Installs a new plugin."""
    validate_plugin(plugin_identifier)
    plugin = get_plugin_from_all(plugin_identifier)
    click.secho("[+] Installing plugin {}...".format(plugin.name), fg="cyan")
    try:
        plugin_manager.install_plugins([plugin])
    except Exception as e:
        click.secho("[-] Couldn't install plugin because of following "
                    "exception: \n{}".format(e), fg="red")


@plugins.command("uninstall")
@click.argument("plugin_identifier")
def uninstall_plugin(plugin_identifier):
    """Uninstalls a plugin from FlaskBB."""
    validate_plugin(plugin_identifier)
    plugin = get_plugin_from_all(plugin_identifier)
    click.secho("[+] Uninstalling plugin {}...".format(plugin.name), fg="cyan")
    try:
        plugin_manager.uninstall_plugins([plugin])
    except AttributeError:
        pass


@plugins.command("remove")
@click.argument("plugin_identifier")
@click.option("--force", "-f", default=False, is_flag=True,
              help="Removes the plugin without asking for confirmation.")
def remove_plugin(plugin_identifier, force):
    """Removes a plugin from the filesystem."""
    validate_plugin(plugin_identifier)
    if not force and not \
            click.confirm(click.style("Are you sure?", fg="magenta")):
        sys.exit(0)

    plugin = get_plugin_from_all(plugin_identifier)
    click.secho("[+] Uninstalling plugin {}...".format(plugin.name), fg="cyan")
    try:
        plugin_manager.uninstall_plugins([plugin])
    except Exception as e:
        click.secho("[-] Couldn't uninstall plugin because of following "
                    "exception: \n{}".format(e), fg="red")
        if not click.confirm(click.style(
            "Do you want to continue anyway?", fg="magenta")
        ):
            sys.exit(0)

    click.secho("[+] Removing plugin from filesystem...", fg="cyan")
    shutil.rmtree(plugin.path, ignore_errors=False, onerror=None)


@plugins.command("list")
def list_plugins():
    """Lists all installed plugins."""
    click.secho("[+] Listing all installed plugins...", fg="cyan")

    # This is subject to change as I am not happy with the current
    # plugin system
    enabled_plugins = get_enabled_plugins()
    disabled_plugins = set(get_all_plugins()) - set(enabled_plugins)
    if len(enabled_plugins) > 0:
        click.secho("[+] Enabled Plugins:", fg="blue", bold=True)
        for plugin in enabled_plugins:
            click.secho("    - {} (version {})".format(
                plugin.name, plugin.version), bold=True
            )
    if len(disabled_plugins) > 0:
        click.secho("[+] Disabled Plugins:", fg="yellow", bold=True)
        for plugin in disabled_plugins:
            click.secho("    - {} (version {})".format(
                plugin.name, plugin.version), bold=True
            )
