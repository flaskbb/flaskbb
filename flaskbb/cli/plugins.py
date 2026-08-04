"""
flaskbb.cli.plugins
~~~~~~~~~~~~~~~~~~~

This module contains all plugin commands.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import os

import click
from alembic.util.exc import CommandError
from flask.cli import with_appcontext

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import FlaskBBCLIError, get_cookiecutter, validate_plugin
from flaskbb.extensions import alembic, pluggy
from flaskbb.plugins.models import PluginRegistry
from flaskbb.plugins.utils import remove_zombie_plugins_from_db
from flaskbb.utils.populate import has_migrations


@flaskbb.group()
def plugins():
    """Plugins command sub group. If you want to do some i18n stuff checkout
    the corresponding command sub group."""
    pass


def _select_plugins(plugin_name: str | None, all_plugins: bool) -> list[PluginRegistry]:
    """Returns the plugins a command should act on - either the single
    named one or, with ``--all``, every plugin known to FlaskBB.
    """
    if all_plugins == bool(plugin_name):
        raise FlaskBBCLIError("Either provide a PLUGIN_NAME or use '--all'.", fg="red")

    if all_plugins:
        return PluginRegistry.get_all()

    validate_plugin(plugin_name)  # pyright: ignore[reportArgumentType]
    plugin = PluginRegistry.get(PluginRegistry.name == plugin_name)
    if plugin is None:
        raise click.Abort()
    return [plugin]


def _select_scope(settings_only: bool, migrations_only: bool) -> tuple[bool, bool]:
    """Returns whether the settings and the migrations should be touched.
    Without either switch both of them are.
    """
    if settings_only and migrations_only:
        raise FlaskBBCLIError(
            "'--settings-only' and '--migrations-only' are mutually exclusive.",
            fg="red",
        )

    return not migrations_only, not settings_only


def _plugin_has_migrations(plugin_name: str) -> bool:
    """A disabled plugin is blocked on pluggy, so its migrations aren't
    part of alembic's version locations and can't be run.
    """
    plugin = pluggy.get_plugin(plugin_name)
    return plugin is not None and has_migrations(plugin)


def _apply_migrations(plugin_name: str):
    if not _plugin_has_migrations(plugin_name):
        return

    try:
        alembic.upgrade(target=f"{plugin_name}@head")
        click.secho(f"[+] Applied the migrations of '{plugin_name}'.", fg="green")
    except CommandError as exc:
        click.secho(
            f"[!] Couldn't apply the migrations of '{plugin_name}': {exc}", fg="red"
        )


def _revert_migrations(plugin_name: str):
    if not _plugin_has_migrations(plugin_name):
        return

    try:
        alembic.downgrade(target=f"{plugin_name}@base")
        click.secho(f"[+] Reverted the migrations of '{plugin_name}'.", fg="green")
    except CommandError as exc:
        click.secho(
            f"[!] Couldn't revert the migrations of '{plugin_name}': {exc}", fg="red"
        )


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
                f"\t- {pluggy.get_name(p_mod)}\t\t({p_dist.project_name}) "
                f"\tversion {p_dist.version}\t settings: {settings_update_str}",
                bold=True,
            )

    disabled_plugins = pluggy.list_disabled_plugins()
    if len(disabled_plugins) > 0:
        click.secho("[+] Disabled Plugins:", fg="yellow", bold=True)
        for plugin in disabled_plugins:
            if not plugin:
                click.secho(f"Plugin not found {plugin}")
                continue
            p_mod = plugin[0]  # pyright: ignore[reportIndexIssue, reportUnknownVariableType]
            p_dist = plugin[1]  # pyright: ignore[reportIndexIssue, reportUnknownVariableType]
            click.secho(
                f"\t- {p_mod.title()}\t({p_dist.key}), version {p_dist.version}",  # pyright: ignore[reportUnknownMemberType]
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
        click.secho(f"Plugin '{plugin.name}' is already enabled.")

    plugin.enabled = True
    plugin.save()
    click.secho(f"[+] Plugin '{plugin.name}' enabled.", fg="green")


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
        click.secho(f"Plugin '{plugin.name}' is already disabled.")

    plugin.enabled = False
    plugin.save()
    click.secho(f"[+] Plugin '{plugin.name}' disabled.", fg="green")


@plugins.command("install")
@click.argument("plugin_name", required=False)
@click.option(
    "--all",
    "-a",
    "all_plugins",
    default=False,
    is_flag=True,
    help="Installs all plugins.",
)
@click.option(
    "--settings-only",
    "-s",
    default=False,
    is_flag=True,
    help="Only installs the settings.",
)
@click.option(
    "--migrations-only",
    "-m",
    default=False,
    is_flag=True,
    help="Only applies the migrations.",
)
@click.option(
    "--force", "-f", default=False, is_flag=True, help="Overwrites existing settings"
)
def install(
    plugin_name: str | None,
    all_plugins: bool,
    settings_only: bool,
    migrations_only: bool,
    force: bool,
):
    """Installs a plugin's settings and applies its migrations."""
    do_settings, do_migrations = _select_scope(settings_only, migrations_only)

    for plugin in _select_plugins(plugin_name, all_plugins):
        if not plugin.enabled:
            click.secho(
                f"[+] Can't install disabled plugin. "
                f"Enable '{plugin.name}' Plugin first.",
                fg="red",
            )
            continue

        if do_settings:
            if plugin.is_installable:
                plugin.add_settings(force)
                click.secho(
                    f"[+] Plugin '{plugin.name}' has been installed.", fg="green"
                )
            else:
                click.secho(f"[+] Nothing to install for '{plugin.name}'.", fg="green")

        if do_migrations:
            _apply_migrations(plugin.name)


@plugins.command("uninstall")
@click.argument("plugin_name", required=False)
@click.option(
    "--all",
    "-a",
    "all_plugins",
    default=False,
    is_flag=True,
    help="Uninstalls all plugins.",
)
@click.option(
    "--settings-only",
    "-s",
    default=False,
    is_flag=True,
    help="Only removes the settings.",
)
@click.option(
    "--migrations-only",
    "-m",
    default=False,
    is_flag=True,
    help="Only reverts the migrations.",
)
@click.option(
    "--force", "-f", default=False, is_flag=True, help="Doesn't ask for confirmation."
)
def uninstall(
    plugin_name: str | None,
    all_plugins: bool,
    settings_only: bool,
    migrations_only: bool,
    force: bool,
):
    """Uninstalls a plugin's settings and reverts its migrations."""
    do_settings, do_migrations = _select_scope(settings_only, migrations_only)
    selected = _select_plugins(plugin_name, all_plugins)

    with_migrations = [p.name for p in selected if _plugin_has_migrations(p.name)]
    if do_migrations and with_migrations and not force:
        click.confirm(
            click.style(
                "Reverting the migrations of {} will drop their data. Continue?".format(
                    ", ".join(with_migrations)
                ),
                fg="magenta",
            ),
            abort=True,
        )

    for plugin in selected:
        if do_migrations:
            _revert_migrations(plugin.name)

        if do_settings:
            if plugin.is_installed:
                plugin.remove_settings()
                click.secho(
                    f"[+] Plugin '{plugin.name}' has been uninstalled.", fg="green"
                )
            else:
                click.secho(
                    f"[+] Nothing to uninstall for '{plugin.name}'.", fg="green"
                )


@plugins.command("upgrade")
@click.argument("plugin_name", required=False)
@click.option(
    "--all",
    "-a",
    "all_plugins",
    default=False,
    is_flag=True,
    help="Upgrades all plugins.",
)
@click.option(
    "--settings-only",
    "-s",
    default=False,
    is_flag=True,
    help="Only upgrades the settings.",
)
@click.option(
    "--migrations-only",
    "-m",
    default=False,
    is_flag=True,
    help="Only applies the migrations.",
)
def upgrade(
    plugin_name: str | None,
    all_plugins: bool,
    settings_only: bool,
    migrations_only: bool,
):
    """Upgrades a plugin's settings and applies its newest migrations."""
    do_settings, do_migrations = _select_scope(settings_only, migrations_only)

    for plugin in _select_plugins(plugin_name, all_plugins):
        if do_settings:
            if plugin.is_installed and plugin.needs_setting_upgrade():
                plugin.upgrade_settings()
                click.secho(
                    f"[+] Plugin '{plugin.name}' has been upgraded.", fg="green"
                )
            else:
                click.secho(
                    f"[+] Plugin '{plugin.name}' has no upgradable settings.",
                    fg="green",
                )

        if do_migrations:
            _apply_migrations(plugin.name)


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

    r = cookiecutter(template, output_dir=out_dir, overwrite_if_exists=force)  # pyright: ignore[reportCallIssue, reportUnknownVariableType]
    click.secho(f"[+] Created new plugin in {r}", fg="green", bold=True)
