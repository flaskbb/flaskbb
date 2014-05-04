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

    @property
    def name(self):
        """If not overridden, it will use the classname as the plugin name."""
        return self.__class__.__name__

    @property
    def description(self):
        """Returns a small description of the plugin."""
        return ""

    @property
    def version(self):
        """Returns the version of the plugin"""
        return "0.0.0"

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
    """Manages all available hooks."""

    def __init__(self):
        self.hooks = {}

    def new(self, name):
        """Creates a new hook.

        :param name: The name of the hook.
        """
        if name not in self.hooks:
            self.hooks[name] = Hook()

    def add(self, name, callback):
        """Adds a callback to the hook. If the hook doesn't exist, it will
        create a new one and add than the callback will be added.

        :param name: The name of the hook.

        :param callback: The callback which should be added to the hook.
        """
        if name not in self.hooks:
            self.new(name)

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
            callback(*args, **kwargs)

hooks = HookManager()
