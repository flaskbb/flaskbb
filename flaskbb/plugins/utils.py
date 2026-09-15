"""
flaskbb.plugins.utils
~~~~~~~~~~~~~~~~~~~~~

This module provides registration and a basic DB backed key-value
store for plugins.

:copyright: (c) 2017 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import traceback
from types import ModuleType
from typing import Any

import sqlalchemy as sa
from flask import flash, redirect, url_for
from flask_babelplus import gettext as _
from markupsafe import Markup

from flaskbb.extensions import alembic, db, pluggy
from flaskbb.plugins.models import PluginRegistry
from flaskbb.utils.datastructures import TemplateEventResult
from flaskbb.utils.populate import has_migrations


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


def plugin_has_pending_migrations(name: str) -> bool:
    """Returns ``True`` if the head revision of the plugin's migration
    branch hasn't been applied to the database yet.
    """
    plugin = pluggy.get_plugin(name)
    # disabled plugins are never imported and their migrations only run once enabled
    if plugin is None or not has_migrations(plugin):
        return False

    script_directory = alembic.script_directory
    current_heads = alembic.migration_context.get_current_heads()
    applied = {
        script.revision for script in script_directory.iterate_revisions(current_heads, "base")
    }
    return any(
        script.revision not in applied for script in script_directory.get_revisions(f"{name}@head")
    )


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
