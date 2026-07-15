# -*- coding: utf-8 -*-
"""
flaskbb.cli.plugins
~~~~~~~~~~~~~~~~~~~

This module contains all plugin commands.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import os
import sys

import click
from flask.cli import with_appcontext

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import get_cookiecutter, validate_plugin
from flaskbb.extensions import pluggy
from flaskbb.plugins.models import PluginRegistry
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
    enabled_plugins = pluggy.list_plugin_distinfo()
    all_plugins = PluginRegistry.get_all()
    if len(enabled_plugins) > 0:
        click.secho("[+] Enabled Plugins:", fg="blue", bold=True)
        for plugin in enabled_plugins:
            if not plugin:
                click.secho(f"Plugin not found {plugin}")
                continue
            p_mod = plugin[0]
            p_dist = plugin[1]
            plugin_reg = next(
                (p for p in all_plugins if p.name == pluggy.get_name(p_mod)), None
            )

            settings_update_str = "up-to-date"
            if plugin_reg:
                settings_diff = plugin_reg.get_setting_diff()

                if settings_diff is not None and settings_diff.has_changes:
                    settings_update_str = f"{settings_diff.log_output}"

            click.secho(
                "\t- {}\t\t({}) \tversion {}\t settings: {}".format(
                    pluggy.get_name(p_mod),
                    p_dist.project_name,
                    p_dist.version,
                    settings_update_str,
                ),
                bold=True,
            )

    disabled_plugins = pluggy.list_disabled_plugins()
    if len(disabled_plugins) > 0:
        click.secho("[+] Disabled Plugins:", fg="yellow", bold=True)
        for plugin in disabled_plugins:
            if not plugin:
                click.secho(f"Plugin not found {plugin}")
                continue
            p_mod = plugin[0]
            p_dist = plugin[1]
            click.secho(
                "\t- {}\t({}), version {}".format(
                    p_mod.title(), p_dist.key, p_dist.version
                ),
                bold=True,
            )


@plugins.command("enable")
@click.argument("plugin_name")
@with_appcontext
def enable_plugin(plugin_name: str):
    """Enables a plugin."""
    validate_plugin(plugin_name)
    plugin = PluginRegistry.get(PluginRegistry.name == plugin_name)
    if plugin is None:
        raise click.Abort()

    if plugin.enabled:
        click.secho("Plugin '{}' is already enabled.".format(plugin.name))

    plugin.enabled = True
    plugin.save()
    click.secho("[+] Plugin '{}' enabled.".format(plugin.name), fg="green")


@plugins.command("disable")
@click.argument("plugin_name")
@with_appcontext
def disable_plugin(plugin_name: str):
    """Disables a plugin."""
    validate_plugin(plugin_name)
    plugin = PluginRegistry.get(PluginRegistry.name == plugin_name)
    if plugin is None:
        raise click.Abort()

    if not plugin.enabled:
        click.secho("Plugin '{}' is already disabled.".format(plugin.name))

    plugin.enabled = False
    plugin.save()
    click.secho("[+] Plugin '{}' disabled.".format(plugin.name), fg="green")


@plugins.command("install")
@click.argument("plugin_name")
@click.option(
    "--force", "-f", default=False, is_flag=True, help="Overwrites existing settings"
)
def install(plugin_name: str, force: bool):
    """Installs a plugin (no migrations)."""
    validate_plugin(plugin_name)
    plugin = PluginRegistry.get(PluginRegistry.name == plugin_name)
    if plugin is None:
        raise click.Abort()

    if not plugin.enabled:
        click.secho(
            "[+] Can't install disabled plugin. Enable '{}' Plugin first.".format(
                plugin.name
            ),
            fg="red",
        )
        sys.exit(0)

    if plugin.is_installable:
        plugin_module = pluggy.get_plugin(plugin.name)
        plugin.add_settings(force)
        click.secho("[+] Plugin has been installed.", fg="green")
    else:
        click.secho("[+] Nothing to install.", fg="green")


@plugins.command("uninstall")
@click.argument("plugin_name")
def uninstall(plugin_name: str):
    """Uninstalls a plugin (no migrations)."""
    validate_plugin(plugin_name)
    plugin = PluginRegistry.get(PluginRegistry.name == plugin_name)
    if plugin is None:
        raise click.Abort()

    if plugin.is_installed:
        plugin.remove_settings()
        click.secho("[+] Plugin has been uninstalled.", fg="green")
    else:
        click.secho("[+] Nothing to uninstall.", fg="green")


@plugins.command("upgrade")
@click.argument("plugin_name")
def upgrade(plugin_name: str):
    """Upgrades a plugin's settings to its newest version"""
    validate_plugin(plugin_name)
    plugin = PluginRegistry.get(PluginRegistry.name == plugin_name)
    if plugin is None:
        raise click.Abort()

    if plugin.is_installed and plugin.needs_setting_upgrade():
        plugin.upgrade_settings()
        click.secho("[+] Plugin has been upgraded.", fg="green")
    else:
        click.secho("[+] Plugin has no upgradable settings.", fg="green")


@plugins.command("cleanup")
@with_appcontext
def cleanup():
    """Removes zombie plugins from FlaskBB.

    A zombie plugin is a plugin
    which exists in the database but isn't installed in the env anymore.
    """
    deleted_plugins = remove_zombie_plugins_from_db()
    if len(deleted_plugins) > 0:
        click.secho(
            "[+] Removed following zombie plugins from FlaskBB: ", fg="green", nl=False
        )
        click.secho("{}".format(", ".join(deleted_plugins)))
    else:
        click.secho("[+] No zombie plugins found.", fg="green")


@plugins.command("new")
@click.option(
    "--template",
    "-t",
    type=click.STRING,
    default="https://github.com/sh4nks/cookiecutter-flaskbb-plugin",
    help="Path to a cookiecutter template or to a valid git repo.",
)
@click.option(
    "--out-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="The location for the new FlaskBB plugin.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Overwrite the contents of output directory if it exists",
)
def new_plugin(template: str, out_dir: str | None, force: bool):
    """Creates a new plugin based on the cookiecutter plugin
    template. Defaults to this template:
    https://github.com/sh4nks/cookiecutter-flaskbb-plugin.
    It will either accept a valid path on the filesystem
    or a URL to a Git repository which contains the cookiecutter template.
    """
    cookiecutter = get_cookiecutter()

    if out_dir is None:
        out_dir = click.prompt("Saving plugin in", default=os.path.abspath("."))

    r = cookiecutter(template, output_dir=out_dir, overwrite_if_exists=force)
    click.secho("[+] Created new plugin in {}".format(r), fg="green", bold=True)
