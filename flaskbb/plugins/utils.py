# -*- coding: utf-8 -*-
"""
flaskbb.plugins.utils
~~~~~~~~~~~~~~~~~~~~~

This module provides registration and a basic DB backed key-value
store for plugins.

:copyright: (c) 2017 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from flask import flash, redirect, url_for
from flask_babelplus import gettext as _
from markupsafe import Markup

from flaskbb.extensions import db, pluggy
from flaskbb.plugins.models import PluginRegistry
from flaskbb.utils.datastructures import TemplateEventResult


def template_hook(name, silent=True, is_markup=True, **kwargs):
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


def validate_plugin(name):
    """Tries to look up the plugin by name. Upon failure it will flash
    a message and abort. Returns the plugin module on success.
    """
    plugin_module = pluggy.get_plugin(name)
    if plugin_module is None:
        flash(_("Plugin %(plugin)s not found.", plugin=name), "error")
        return redirect(url_for("management.plugins"))
    return plugin_module


def remove_zombie_plugins_from_db():
    """Removes 'zombie' plugins from the db. A zombie plugin is a plugin
    which exists in the database but isn't installed in the env anymore.
    Returns the names of the deleted plugins.
    """
    d_fs_plugins: list[str] = [p[0] for p in pluggy.list_disabled_plugins()]
    d_db_plugins = (
        db.session.execute(db.select(PluginRegistry.name).filter_by(enabled=False))
        .scalars()
        .all()
    )

    plugin_names = db.session.execute(db.select(PluginRegistry.name)).scalars().all()

    remove_me: list[str] = []
    for p in plugin_names:
        if p in d_db_plugins and p not in d_fs_plugins:
            remove_me.append(p)

    if len(remove_me) > 0:
        db.session.execute(
            db.delete(PluginRegistry).filter(PluginRegistry.name.in_(remove_me))
        )
        db.session.commit()
    return remove_me
