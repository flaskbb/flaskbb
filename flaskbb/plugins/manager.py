# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.manager
    ~~~~~~~~~~~~~~~~~~~~~~~

    The Plugin manager.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import os
from werkzeug.utils import import_string


class PluginManager(object):

    def __init__(self, app=None, **kwargs):
        """Initializes the PluginManager. It is also possible to initialize the
        PluginManager via a factory. For example::

            plugin_manager = PluginManager()
            plugin_manager.init_app(app)

        :param app: The flask application. It is needed to do plugin
                    specific things like registering additional views or
                    doing things where the application context is needed.

        :param plugin_folder: The plugin folder where the plugins resides.

        :param base_plugin_package: The plugins package name. It is usually the
                                    same like the plugin_folder.
        """
        if app is not None:
            self.init_app(app, **kwargs)

        # All loaded plugins
        self._plugins = []

        # All found plugins
        self._found_plugins = []

    def init_app(self, app, plugin_folder="plugins",
                 base_plugin_package="plugins"):
        self.app = app
        self.plugin_folder = os.path.join(self.app.root_path, plugin_folder)
        self.base_plugin_package = ".".join(
            [self.app.name, base_plugin_package]
        )

    @property
    def plugins(self):
        """Returns all loaded plugins. You still need to enable them."""
        if not len(self._plugins):
            self._plugins = self.load_plugins()
        return self._plugins

    def __getitem__(self, name):
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        raise KeyError("Plugin %s is not known" % name)

    def load_plugins(self):
        """Loads all plugins. They are still disabled.
        Returns a list with all loaded plugins. They should now be accessible
        via self.plugins.
        """
        plugins = []
        for plugin in self.iter_plugins():
            plugins.append(plugin)

        return plugins

    def iter_plugins(self):
        """Iterates over all possible plugins found in ``self.find_plugins()``,
        imports them and if the import succeeded it will yield the plugin class.
        """
        for plugin in self.find_plugins():
            plugin_class = import_string(plugin)

            if plugin_class is not None:
                yield plugin_class

    def find_plugins(self):
        """Find all possible plugins in the plugin folder."""
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
                    self._found_plugins.append(plugin)
                except AttributeError:
                    pass

        return self._found_plugins

    def install_plugins(self, plugins=None):
        """Install all or selected plugins.

        :param plugins: An iterable with plugins. If no plugins are passed
                        it will try to install all plugins.
        """
        for plugin in plugins or self.plugins:
            with self.app.app_context():
                plugin().install()

    def uninstall_plugins(self, plugins=None):
        """Uninstall the plugin.

        :param plugins: An iterable with plugins. If no plugins are passed
                        it will try to uninstall all plugins.
        """
        for plugin in plugins or self.plugins:
            with self.app.app_context():
                plugin().uninstall()

    def enable_plugins(self, plugins=None):
        """Enable all or selected plugins.

        :param plugins: An iterable with plugins. If no plugins are passed
                        it will try to enable all plugins.
        """
        for plugin in plugins or self.plugins:
            with self.app.app_context():
                plugin().enable()

    def disable_plugins(self, plugins=None):
        """Disable all or selected plugins.

        :param plugins: An iterable with plugins. If no plugins are passed
                        it will try to disable all plugins.
        """
        for plugin in plugins or self.plugins:
            with self.app.app_context():
                plugin().disable()
