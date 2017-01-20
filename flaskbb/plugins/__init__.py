# -*- coding: utf-8 -*-
"""
    flaskbb.plugins
    ~~~~~~~~~~~~~~~

    This module contains the Plugin class used by all Plugins for FlaskBB.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import current_app
from flask_plugins import Plugin
from flask_migrate import upgrade,downgrade,migrate
from flaskbb.extensions import db,migrate as mig
from flaskbb.management.models import SettingsGroup
from flask import g
import contextlib
import os,copy

@contextlib.contextmanager
def plugin_name_migrate(name):
    g.plugin_name=name
    yield
    del g.plugin_name

def db_for_plugin(plugin_name,db):
    newdb=copy.copy(db)
    def Table(*args,**kwargs):
        newtable=db.Table(*args,**kwargs)
        newtable._plugin=plugin_name
        return newtable
    newdb.Table=Table
    return newdb

@mig.configure
def config_migrate(config):
    plugins = current_app.extensions['plugin_manager'].all_plugins.values()
    migration_dirs = [p.get_migration_version_dir() for p in plugins]
    if config.get_main_option('version_table')=='plugins':
        config.set_main_option('version_locations', ' '.join(migration_dirs))
    return config


class FlaskBBPlugin(Plugin):

    #: This is the :class:`SettingsGroup` key - if your the plugin needs to
    #: install additional things you must set it, else it won't install
    #: anything.
    settings_key = None

    def resource_filename(self, *names):
        return os.path.join(self.path, *names)

    def get_migration_version_dir(self):
        return self.resource_filename('migration_versions')

    def upgrade_database(self, target='head'):
        plugindir = current_app.extensions['plugin_manager'].plugin_folder
        upgrade(directory=os.path.join(plugindir, 'migrations'), revision=self.settings_key + '@' + target)

    def downgrade_database(self, target='base'):
        plugindir = current_app.extensions['plugin_manager'].plugin_folder
        downgrade(directory=os.path.join(plugindir, 'migrations'), revision=self.settings_key + '@' + target)

    def migrate(self):
        with plugin_name_migrate(self.__module__):
            plugindir = current_app.extensions['plugin_manager'].plugin_folder
            try:
                migrate(directory=os.path.join(plugindir, 'migrations'),
                        head=self.settings_key)
            except Exception as e:  #presumably this is the initial migration?
                migrate(directory=os.path.join(plugindir, 'migrations'),
                        version_path=self.resource_filename('migration_versions'),
                        branch_label=self.settings_key)

    @property
    def installable(self):
        """Is ``True`` if the Plugin can be installed."""
        if self.settings_key is not None:
            return True
        return False

    @property
    def uninstallable(self):
        """Is ``True`` if the Plugin can be uninstalled."""
        if self.installable:
            group = SettingsGroup.query.\
                filter_by(key=self.settings_key).\
                first()
            if group and len(group.settings.all()) > 0:
                return True
            return False
        return False

        # Some helpers
    def register_blueprint(self, blueprint, **kwargs):
        """Registers a blueprint.

        :param blueprint: The blueprint which should be registered.
        """
        current_app.register_blueprint(blueprint, **kwargs)

    def create_table(self, model, db):
        """Creates the relation for the model

        :param model: The Model which should be created
        :param db: The database instance.
        """
        if not model.__table__.exists(bind=db.engine):
            model.__table__.create(bind=db.engine)

    def drop_table(self, model, db):
        """Drops the relation for the bounded model.

        :param model: The model on which the table is bound.
        :param db: The database instance.
        """
        model.__table__.drop(bind=db.engine)

    def create_all_tables(self, models, db):
        """A interface for creating all models specified in ``models``.

        :param models: A list with models
        :param db: The database instance
        """
        for model in models:
            self.create_table(model, db)

    def drop_all_tables(self, models, db):
        """A interface for dropping all models specified in the
        variable ``models``.

        :param models: A list with models
        :param db: The database instance.
        """
        for model in models:
            self.drop_table(model, db)
