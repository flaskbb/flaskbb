# -*- coding: utf-8 -*-
"""
    flaskbb.plugins
    ~~~~~~~~~~~~~~~

    The Plugin class that every plugin should implement

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""


class PluginError(Exception):
    """Error class for all plugin errors."""
    pass


class Plugin(object):
    """Every plugin should implement this class. It handles the registration
    for the plugin hooks, creates or modifies additional relations or
    registers plugin specific thinks"""

    #: If you want create your tables with one command, put your models
    #: in here.
    models = []

    #: The plugin name
    name = None

    #: The author of the plugin
    author = None

    #: The license of the plugin
    license = None

    #: A small description of the plugin.
    description = None

    #: The version of the plugin"""
    version = "0.0.0"

    def enable(self):
        """Enable the plugin."""
        raise NotImplementedError("{} has not implemented the "
                                  "enable method".format(self.name))

    def disable(self):
        """Disable the plugin."""
        raise NotImplementedError("{} has not implemented the "
                                  "disable method".format(self.name))

    def install(self):
        """The plugin should specify here what needs to be installed.
        For example, create the database and register the hooks."""
        raise NotImplementedError("{} has not implemented the "
                                  "install method".format(self.name))

    def uninstall(self):
        """Uninstalls the plugin and deletes the things that
        the plugin has installed."""
        raise NotImplementedError("{} has not implemented the "
                                  "uninstall method".format(self.name))

    # Some helpers
    def create_table(self, model, db):
        """Creates the table for the model

        :param model: The Model which should be created
        :param db: The database instance.
        """
        if not model.__table__.exists(bind=db.engine):
            model.__table__.create(bind=db.engine)

    def drop_table(self, model, db):
        """Drops the table for the bounded model.

        :param model: The model on which the table is bound.
        :param db: The database instance.
        """
        model.__table__.drop(bind=db.engine)

    def create_all_tables(self, db):
        """A interface for creating all models specified in ``models``.
        If no models are specified in that variable it will abort
        with a exception.

        :param db: The database instance
        """
        if len(self.models) > 0:
            for model in self.models:
                self.create_table(model, db)
        else:
            raise PluginError("No models found in 'models'.")

    def drop_all_tables(self, db):
        """A interface for dropping all models specified in the
        variable ``models``. If no models are specified in that variable,
        it will abort with an exception.

        :param db: The database instance.
        """
        if len(self.models) > 0:
            for model in self.models:
                self.drop_table(model, db)
        else:
            raise PluginError("No models found in 'models'.")


class HookManager(object):
    """Manages all available hooks.

    A new hook can be created like this::

        hooks.new("testHook")

    To add a callback to the hook you need to do that::

        hooks.add("testHook", test_callback)

    If you want to use the last method, you'd also need to pass a callback over
    to the ``add`` method.
    Then you might want to add somewhere in your code the ``caller`` where all
    registered callbacks for the specified hook are going to be called.
    For example::

        def hello():
            do_stuff_here()

            hooks.call("testHook")

            do_more_stuff_here()
    """

    def __init__(self):
        self.hooks = {}

    def new(self, name, hook):
        """Creates a new hook.

        :param name: The name of the hook.
        """
        if name not in self.hooks:
            self.hooks[name] = hook

    def add(self, name, callback):
        """Adds a callback to the hook.

        :param name: The name of the hook.

        :param callback: The callback which should be added to the hook.
        """
        return self.hooks[name].add(callback)

    def remove(self, name, callback):
        """Removes a callback from the hook.

        :param name: The name of the hook.

        :param callback: The callback which should be removed
        """
        self.hooks[name].remove(callback)

    def call(self, name, *args, **kwargs):
        """Calls all callbacks from a named hook with the given arguments.

        :param name: The name of the hook.
        """
        return self.hooks[name].call(*args, **kwargs)


class Hook(object):
    """Represents a hook."""

    def __init__(self):
        self.callbacks = []

    def add(self, callback):
        """Adds a callback to a hook"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
        return callback

    def remove(self, callback):
        """Removes a callback from a hook"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def call(self, *args, **kwargs):
        """Runs all callbacks for the hook."""
        for callback in self.callbacks:
            return callback(*args, **kwargs)

hooks = HookManager()
hooks.new("beforeIndex", Hook())
hooks.new("beforeBreadcrumb", Hook())
