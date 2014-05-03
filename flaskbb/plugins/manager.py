# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.manager
    ~~~~~~~~~~~~~~~~~~~~~~~

    The Plugin loader.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import os
from werkzeug.utils import import_string


class PluginManager(object):

    def __init__(self, app):
        self.app = app
        self.plugin_folder = os.path.join(self.app.root_path, "plugins")
        self.base_plugin_package = ".".join([self.app.name, "plugins"])

        self.found_plugins = []
        self.plugins = []

    def __getitem__(self, name):
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        raise KeyError("Plugin %s is not known" % name)

    def register_blueprints(self, blueprint):
        self.app.register_blueprints(blueprint)

    def load_plugins(self):
        """Loads and install all found plugins.
        TODO: Only load/install activated plugins
        """
        self.find_plugins()

        for plugin in self.iter_plugins():
            with self.app.app_context():
                plugin().install()

        #self.enable_plugins(self.plugins)

    def iter_plugins(self):
        for plugin in self.found_plugins:
            plugin_class = import_string(plugin)

            if plugin_class is not None:
                self.plugins.append(plugin)
                yield plugin_class

    def find_plugins(self):
        for item in os.listdir(self.plugin_folder):

            if os.path.isdir(os.path.join(self.plugin_folder, item)) and \
                    os.path.exists(
                        os.path.join(self.plugin_folder, item, "__init__.py")):

                plugin = ".".join([self.base_plugin_package, item])

                # Same like from flaskbb.plugins.pluginname import __plugin__
                tmp = __import__(
                    plugin, globals(), locals(), ["__plugin__"], -1
                )
                try:
                    plugin = "{}.{}".format(plugin, tmp.__plugin__)
                    self.found_plugins.append(plugin)
                except AttributeError:
                    pass

    def enable_plugins(self, plugins=None):
        """Enable all or selected plugins."""

        for plugin in plugins or self.plugins:
            plugin.enable()

    def disable_plugins(self, plugins=None):
        """Disable all or selected plugins."""

        for plugin in plugins or self.plugins:
            plugin.disable()


"""
for ipython:
from flask import current_app
from flaskbb.plugins import Plugin
from flaskbb.plugins.manager import PluginManager
manager = PluginLoader(current_app)
manager.find_plugins()
manager.plugins
"""
