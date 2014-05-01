# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.loader
    ~~~~~~~~~~~~~~~~~~~~~~

    The Plugin loader.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import os


class PluginLoader(object):

    #: Stores all founded plugins in the plugins folder
    plugins = list()

    def __init__(self, app):
        self.app = app
        self.plugin_folder = os.path.join(self.app.root_path, "plugins")
        self.base_plugin_package = ".".join([self.app.name, "plugins"])

    def load_plugins(self):
        """Loads all plugins"""
        #from flaskbb.plugins.pluginname import PluginName
        #__import__(plugin, globals(), locals(), [tmp.__plugin__], -1)
        pass

    def check_plugin(self, plugin):
        """Checks if a plugin is appropriate.

        :param plugin:
        """
        pass

    def find_plugins(self):
        for item in os.listdir(self.plugin_folder):

            if os.path.isdir(os.path.join(self.plugin_folder, item)) and \
                    os.path.exists(
                        os.path.join(self.plugin_folder, item, "__init__.py")):

                plugin = ".".join([self.base_plugin_package, item])

                # Same like from flaskbb.plugins.pluginname import __plugin__
                tmp = __import__(
                    plugin, globals(), locals(), ['__plugin__'], -1
                )

                self.plugins.append(tmp.__plugin__)

"""
for ipython:
from flask import current_app
from flaskbb.plugins.loader import PluginLoader
loader = PluginLoader(current_app)
loader.find_plugins()
loader.plugins
"""
