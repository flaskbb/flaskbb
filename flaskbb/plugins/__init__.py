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

    #: The name of the plugin
    #: E.g. "Example Plugin"
    name = None

    #: A small description of the plugin
    description = None

    def install(self, app=None):
        """The plugin should specify here what needs to be installed.
        For example, create the database and register the hooks."""
        raise NotImplementedError

    def uninstall(self, app=None):
        """Uninstalls the plugin and deletes the things that
        the plugin has installed."""
        raise NotImplementedError

    def create_table(self, model, db):
        """Creates the table for the model

        :param model: The Model which should be created
        :param db: The database instance.
        """
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
