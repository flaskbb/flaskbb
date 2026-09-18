"""
flaskbb.plugins.utils
~~~~~~~~~~~~~~~~~~~~~

This module provides registration and a basic DB backed key-value
store for plugins.

:copyright: (c) 2017 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import importlib.metadata
import importlib.util
import logging
import os
import traceback
from collections.abc import Iterable
from types import ModuleType
from typing import Any, cast

import sqlalchemy as sa
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from alembic.script.revision import RevisionError
from flask import flash, redirect, url_for
from flask_babelplus import gettext as _
from markupsafe import Markup

from flaskbb.core.app import FlaskBB
from flaskbb.extensions import alembic, db, pluggy
from flaskbb.plugins.models import PluginRegistry
from flaskbb.utils.datastructures import TemplateEventResult

logger = logging.getLogger(__name__)


def plugin_migrations_dir(entry_point: importlib.metadata.EntryPoint) -> str | None:
    """Looks up the plugin's migrations next to its package without importing
    it, the convention ``has_migrations`` relies on as well.
    """
    package = importlib.util.find_spec(entry_point.module.split(".")[0])
    if package is None or not package.submodule_search_locations:
        return None
    migrations = os.path.join(next(iter(package.submodule_search_locations)), "migrations")
    return migrations if os.path.isdir(migrations) else None


def plugins_with_pending_migrations(
    app: FlaskBB,
    entry_points: Iterable[importlib.metadata.EntryPoint],
    names: set[str],
) -> set[str]:
    """Returns the plugins out of ``names`` with migrations that haven't been
    applied yet. The plugins aren't loaded and alembic isn't configured yet,
    so the revisions are read from the migration directories directly.
    """
    if not names:
        return set()

    script_location = cast(str, app.config["ALEMBIC"]["script_location"])
    if not os.path.isabs(script_location) and ":" not in script_location:
        script_location = os.path.join(app.root_path, script_location)
    plugin_dirs = [d for ep in entry_points if (d := plugin_migrations_dir(ep)) is not None]
    script_directory = ScriptDirectory(
        script_location, version_locations=[script_location, *plugin_dirs]
    )

    with app.app_context(), db.engine.connect() as connection:
        current_heads = MigrationContext.configure(connection).get_current_heads()

    try:
        applied = {
            script.revision for script in script_directory.iterate_revisions(current_heads, "base")
        }
        return {
            name
            for script in script_directory.walk_revisions()
            if script.revision not in applied
            for name in names & script.branch_labels
        }
    except RevisionError as exc:
        # e.g. the database holds a revision of a plugin that was removed from the env
        logger.warning("Couldn't check the plugins for pending migrations.", exc_info=exc)
        return set()


def template_hook(name: str, silent: bool = True, is_markup: bool = True, **kwargs: Any):
    """Calls the given template hook.

    :param name: The name of the hook.
    :param silent: If set to ``False``, it will raise an exception if a hook
                   doesn't exist. Defauls to ``True``.
    :param is_markup: Determines if the hook should return a Markup object or
                   not. Setting to False returns a TemplateEventResult object.
                   The default is True.
    :param kwargs: Additional kwargs that should be passed to the hook.
    """
    try:
        hook = getattr(pluggy.hook, name)
        result = TemplateEventResult(hook(**kwargs))
    except AttributeError:  # raised if hook doesn't exist
        if silent:
            return ""
        raise

    if is_markup:
        return Markup(result)

    return result


def validate_plugin(name: str):
    """Tries to look up the plugin by name. Upon failure it will flash
    a message and abort. Returns the plugin module on success.
    """
    # list_name also holds the disabled plugins, get_plugin returns None for them
    if name not in pluggy.list_name():
        flash(_("Plugin %(plugin)s not found.", plugin=name), "error")
        return redirect(url_for("management.plugins"))
    return pluggy.get_plugin(name)


def remove_zombie_plugins_from_db():
    """Removes 'zombie' plugins from the db. A zombie plugin is a plugin
    which exists in the database but isn't installed in the env anymore.
    Returns the names of the deleted plugins.
    """
    d_fs_plugins = set(pluggy.get_disabled_plugins())
    d_db_plugins = (
        db.session.execute(sa.select(PluginRegistry.name).filter_by(enabled=False)).scalars().all()
    )

    plugin_names = db.session.execute(sa.select(PluginRegistry.name)).scalars().all()

    remove_me: list[str] = []
    for p in plugin_names:
        if p in d_db_plugins and p not in d_fs_plugins:
            remove_me.append(p)

    if len(remove_me) > 0:
        db.session.execute(sa.delete(PluginRegistry).filter(PluginRegistry.name.in_(remove_me)))
        db.session.commit()
    return remove_me


def plugin_has_migrations(name: str) -> bool:
    """Returns ``True`` if the plugin ships a migration branch. Unlike
    ``has_migrations`` this works for disabled plugins as well, because their
    migrations are part of alembic's version locations too.
    """
    return any(name in script.branch_labels for script in alembic.script_directory.walk_revisions())


def apply_plugin_migrations(name: str) -> bool:
    """Upgrades the plugin's migration branch to its head. Returns ``False``
    if the plugin has no migrations.
    """
    if not plugin_has_migrations(name):
        return False

    alembic.upgrade(target=f"{name}@head")
    return True


def revert_plugin_migrations(name: str) -> bool:
    """Downgrades the plugin's migration branch to its base, which drops its
    tables and data. Returns ``False`` if the plugin has no migrations.
    """
    if not plugin_has_migrations(name):
        return False

    alembic.downgrade(target=f"{name}@base")
    return True


def plugin_has_pending_migrations(name: str) -> bool:
    """Returns ``True`` if the head revision of the plugin's migration
    branch hasn't been applied to the database yet.
    """
    if not plugin_has_migrations(name):
        return False

    applied = _applied_revisions()
    return any(
        script.revision not in applied
        for script in alembic.script_directory.get_revisions(f"{name}@head")
    )


def plugin_has_applied_migrations(name: str) -> bool:
    """Returns ``True`` if any revision of the plugin's migration branch has
    been applied to the database. Works for disabled plugins as well.
    """
    if not plugin_has_migrations(name):
        return False

    applied = _applied_revisions()
    return any(
        script.revision in applied
        for script in alembic.script_directory.walk_revisions()
        if name in script.branch_labels
    )


def plugin_tables_in_use(name: str) -> bool:
    """Returns ``True`` if the plugin is loaded in this process and its tables
    exist. Its running code keeps using them, e.g. the columns a plugin adds
    to users would break every page once dropped.
    """
    return pluggy.get_plugin(name) is not None and plugin_has_applied_migrations(name)


def _applied_revisions() -> set[str]:
    current_heads = alembic.migration_context.get_current_heads()
    return {
        script.revision
        for script in alembic.script_directory.iterate_revisions(current_heads, "base")
    }


def get_plugins_with_pending_migrations(error: BaseException) -> list[str]:
    """Returns the names of the external plugins whose code raised ``error``
    and whose migrations haven't been applied yet.
    """
    external = pluggy.get_external_plugins()
    packages = {
        plugin.__name__.split(".")[0]: name
        for name, plugin in pluggy.list_name_plugin()
        if plugin in external and isinstance(plugin, ModuleType)
    }
    raising = {
        packages[package]
        for frame, _lineno in traceback.walk_tb(error.__traceback__)
        if (package := frame.f_globals.get("__name__", "").split(".")[0]) in packages
    }
    return sorted(name for name in raising if plugin_has_pending_migrations(name))
