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
from flask_babelplus import gettext as _

def validate_plugin(name):
    """Tries to look up the plugin by name. Upon failure it will flash
    a message and abort. Returns the plugin module on success.
    """
    plugin_module = current_app.pluggy.get_plugin(name)
    if plugin_module is None:
        flash(_("Plugin %(plugin)s not found.", plugin=name), "error")
        return redirect(url_for("management.plugins"))
    return plugin_module
