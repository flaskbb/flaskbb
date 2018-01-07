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

import click
from flask import current_app
from flask.cli import with_appcontext

from flaskbb.extensions import db
from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import validate_plugin, get_cookiecutter
from flaskbb.plugins.models import PluginRegistry, PluginStore
from flaskbb.plugins.utils import remove_zombie_plugins_from_db


@flaskbb.group()
def plugins():
    """Plugins command sub group. If you want to run migrations or do some
    i18n stuff checkout the corresponding command sub groups."""
    pass


@plugins.command("list")
@with_appcontext
def list_plugins():
    """Lists all installed plugins."""
    enabled_plugins = current_app.pluggy.list_plugin_distinfo()
    if len(enabled_plugins) > 0:
        click.secho("[+] Enabled Plugins:", fg="blue", bold=True)
        for plugin in enabled_plugins:
            p_mod = plugin[0]
            p_dist = plugin[1]
            click.secho("\t- {}\t({}), version {}".format(
                current_app.pluggy.get_name(p_mod).title(), p_dist.key,
                p_dist.version), bold=True
            )

    disabled_plugins = current_app.pluggy.list_disabled_plugins()
    if len(disabled_plugins) > 0:
        click.secho("[+] Disabled Plugins:", fg="yellow", bold=True)
        for plugin in disabled_plugins:
            p_mod = plugin[0]
            p_dist = plugin[1]
            click.secho("\t- {}\t({}), version {}".format(
                p_mod.title(), p_dist.key,
                p_dist.version), bold=True
            )


@plugins.command("enable")
@click.argument("plugin_name")
@with_appcontext
def enable_plugin(plugin_name):
    """Enables a plugin."""
    validate_plugin(plugin_name)
    plugin = PluginRegistry.query.filter_by(name=plugin_name).first_or_404()

    if plugin.enabled:
        click.secho("Plugin '{}' is already enabled.".format(plugin.name))

    plugin.enabled = True
    plugin.save()
    click.secho("[+] Plugin '{}' enabled.".format(plugin.name), fg="green")


@plugins.command("disable")
@click.argument("plugin_name")
@with_appcontext
def disable_plugin(plugin_name):
    """Disables a plugin."""
    validate_plugin(plugin_name)
    plugin = PluginRegistry.query.filter_by(name=plugin_name).first_or_404()

    if not plugin.enabled:
        click.secho("Plugin '{}' is already disabled.".format(plugin.name))

    plugin.enabled = False
    plugin.save()
    click.secho("[+] Plugin '{}' disabled.".format(plugin.name), fg="green")


@plugins.command("install")
@click.argument("plugin_name")
@click.option("--force", "-f", default=False, is_flag=True,
              help="Overwrites existing settings")
def install(plugin_name, force):
    """Installs a plugin (no migrations)."""
    validate_plugin(plugin_name)
    plugin = PluginRegistry.query.filter_by(name=plugin_name).first_or_404()

    if not plugin.enabled:
        click.secho("[+] Can't install disabled plugin. "
                    "Enable '{}' Plugin first.".format(plugin.name), fg="red")
        sys.exit(0)

    if plugin.is_installable:
        plugin_module = current_app.pluggy.get_plugin(plugin.name)
        plugin.add_settings(plugin_module.SETTINGS, force)
        click.secho("[+] Plugin has been installed.", fg="green")
    else:
        click.secho("[+] Nothing to install.", fg="green")


@plugins.command("uninstall")
@click.argument("plugin_name")
def uninstall(plugin_name):
    """Uninstalls a plugin (no migrations)."""
    validate_plugin(plugin_name)
    plugin = PluginRegistry.query.filter_by(name=plugin_name).first_or_404()

    if plugin.is_installed:
        PluginStore.query.filter_by(plugin_id=plugin.id).delete()
        db.session.commit()
        click.secho("[+] Plugin has been uninstalled.", fg="green")
    else:
        click.secho("[+] Nothing to uninstall.", fg="green")


@plugins.command("cleanup")
@with_appcontext
def cleanup():
    """Removes zombie plugins from FlaskBB.

    A zombie plugin is a plugin
    which exists in the database but isn't installed in the env anymore.
    """
    deleted_plugins = remove_zombie_plugins_from_db()
    if len(deleted_plugins) > 0:
        click.secho("[+] Removed following zombie plugins from FlaskBB: ",
                    fg="green", nl=False)
        click.secho("{}".format(", ".join(deleted_plugins)))
    else:
        click.secho("[+] No zombie plugins found.", fg="green")


@plugins.command("new")
@click.option("--template", "-t", type=click.STRING,
              default="https://github.com/sh4nks/cookiecutter-flaskbb-plugin",
              help="Path to a cookiecutter template or to a valid git repo.")
@click.option("--out-dir", "-o", type=click.Path(), default=None,
              help="The location for the new FlaskBB plugin.")
@click.option("--force", "-f", is_flag=True, default=False,
              help="Overwrite the contents of output directory if it exists")
def new_plugin(template, out_dir, force):
    """Creates a new plugin based on the cookiecutter plugin
    template. Defaults to this template:
    https://github.com/sh4nks/cookiecutter-flaskbb-plugin.
    It will either accept a valid path on the filesystem
    or a URL to a Git repository which contains the cookiecutter template.
    """
    cookiecutter = get_cookiecutter()

    if out_dir is None:
        out_dir = click.prompt("Saving plugin in",
                               default=os.path.abspath("."))

    r = cookiecutter(template, output_dir=out_dir, overwrite_if_exists=force)
    click.secho("[+] Created new plugin in {}".format(r),
                fg="green", bold=True)
