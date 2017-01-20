# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.plugin_name.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the plugin_name view.

    :copyright: (c) 2016 by Your Name.
    :license: BSD License, see LICENSE for more details.
"""
from flask import Blueprint
from flask_plugins import get_plugin_from_all

from flaskbb.utils.helpers import render_template

# You can modify this to your liking
plugin_bp = Blueprint("plugin_name", __name__, template_folder="templates")


def inject_navigation_link():
    return render_template("navigation_link.html")


@plugin_bp.route("/")
def index():
    plugin_obj = get_plugin_from_all("plugin_name")
    return render_template("plugin_name.html", plugin_obj=plugin_obj)
