# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.utils
    ~~~~~~~~~~~~~~~~~~~~~

    This module provides registration and a basic DB backed key-value
    store for plugins.

    :copyright: (c) 2017 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import current_app, flash, redirect, url_for
from jinja2 import Markup,contextfunction
from flask_babelplus import gettext as _

from flaskbb.extensions import db
from flaskbb.utils.datastructures import TemplateEventResult
from flaskbb.plugins.models import PluginRegistry

@contextfunction
def template_hook(ctx,name, silent=True, **kwargs):
    """Calls the given template hook.

    :param name: The name of the hook.
    :param silent: If set to ``False``, it will raise an exception if a hook
                   doesn't exist. Defauls to ``True``.
    :param kwargs: Additional kwargs that should be passed to the hook.
    """
    kwargs['context']=ctx
    try:
        hook = getattr(current_app.pluggy.hook, name)
        result = hook(**kwargs)
    except AttributeError:  # raised if hook doesn't exist
        if silent:
            return ""
        raise

    return Markup(TemplateEventResult(result))


def validate_plugin(name):
    """Tries to look up the plugin by name. Upon failure it will flash
    a message and abort. Returns the plugin module on success.
    """
    plugin_module = current_app.pluggy.get_plugin(name)
    if plugin_module is None:
        flash(_("Plugin %(plugin)s not found.", plugin=name), "error")
        return redirect(url_for("management.plugins"))
    return plugin_module


def remove_zombie_plugins_from_db():
    """Removes 'zombie' plugins from the db. A zombie plugin is a plugin
    which exists in the database but isn't installed in the env anymore.
    Returns the names of the deleted plugins.
    """
    d_fs_plugins = [p[0] for p in current_app.pluggy.list_disabled_plugins()]
    d_db_plugins = [p.name for p in PluginRegistry.query.filter_by(enabled=False).all()]

    plugin_names = [p.name for p in PluginRegistry.query.all()]

    remove_me = []
    for p in plugin_names:
        if p in d_db_plugins and p not in d_fs_plugins:
            remove_me.append(p)

    if len(remove_me) > 0:
        PluginRegistry.query.filter(
            PluginRegistry.name.in_(remove_me)
        ).delete(synchronize_session='fetch')
        db.session.commit()
    return remove_me
