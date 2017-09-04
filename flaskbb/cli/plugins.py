# -*- coding: utf-8 -*-
"""
    flaskbb.cli.plugins
    ~~~~~~~~~~~~~~~~~~~

    This module contains all plugin commands.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import pluggy
import click
from flask import current_app

from flaskbb.cli.main import flaskbb


@flaskbb.group()
def plugins():
    """Plugins command sub group."""
    pass


@plugins.command("list")
def list_plugins():
    """Lists all installed plugins."""
    click.secho("[+] Listing all installed plugins...", fg="cyan")

    enabled_plugins = current_app.pluggy.list_plugin_distinfo()
    if len(enabled_plugins) > 0:
        click.secho("[+] Enabled Plugins:", fg="blue", bold=True)
        for plugin in enabled_plugins:
            # plugin[0] is the module
            plugin = plugin[1]
            click.secho("    - {} (version {})".format(
                plugin.key, plugin.version), bold=True
            )

    # TODO: is there a better way for doing this?
    pm = pluggy.PluginManager('flaskbb', implprefix='flaskbb_')
    pm.load_setuptools_entrypoints('flaskbb_plugins')
    all_plugins = pm.list_plugin_distinfo()
    disabled_plugins = set(all_plugins) - set(enabled_plugins)
    if len(disabled_plugins) > 0:
        click.secho("[+] Disabled Plugins:", fg="yellow", bold=True)
        for plugin in disabled_plugins:
            plugin = plugin[1]
            click.secho("    - {} (version {})".format(
                plugin.key, plugin.version), bold=True
            )
