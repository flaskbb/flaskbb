# -*- coding: utf-8 -*-
"""
    flaskbb.plugins
    ~~~~~~~~~~~~~~~

    This module contains the Plugin class used by all Plugins for FlaskBB.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import contextlib
import copy
import os

from flask import current_app
from flask import g
from flask_migrate import upgrade, downgrade, migrate
from flask_plugins import Plugin
from flaskbb.extensions import db, migrate as migrate_ext
from flaskbb.management.models import SettingsGroup, Setting


@contextlib.contextmanager  # TODO: Add tests
def plugin_name_migrate(name):
    """Migrations in this with block will only apply to models
    from the named plugin"""
    g.plugin_name = name
    yield
    del g.plugin_name


def db_for_plugin(plugin_name, sqla_instance=None):
    """Labels models as belonging to this plugin.
    sqla_instance is a valid Flask-SQLAlchemy instance, if None,
    then the default db is used

    Usage:
        from flaskbb.plugins import db_for_plugin

        db = db_for_plugin(__name__)

        mytable = db.Table(...)

        class MyModel(db.Model):
            ...
    """
    sqla_instance = sqla_instance or db
    new_db = copy.copy(sqla_instance)

    def Table(*args, **kwargs):
        new_table = sqla_instance.Table(*args, **kwargs)
        new_table._plugin = plugin_name
        return new_table

    new_db.Table = Table
    return new_db


@migrate_ext.configure
def config_migrate(config):
    """Configuration callback for plugins environment."""
    plugins = current_app.extensions['plugin_manager'].all_plugins.values()
    migration_dirs = [p.get_migration_version_dir() for p in plugins]
    if config.get_main_option('version_table') == 'plugins':
        config.set_main_option('version_locations', ' '.join(migration_dirs))
        # current_app.logger.debug(config.get_main_option('version_locations'))
    return config


class FlaskBBPlugin(Plugin):
    #: This is the :class:`SettingsGroup` key - if your the plugin needs to
    #: install additional things you must set it, else it won't install
    #: anything.
    settings_key = None
    requires_install = None

    def resource_filename(self, *names):
        """Returns an absolute filename for a plugin resource."""
        if len(names) == 1 and '/' in names[0]:
            names = names[0].split('/')
        fname = os.path.join(self.path, *names)
        if ' ' in fname and '"' not in fname and "'" not in fname:
            fname = '"%s"' % fname
        return fname

    def get_migration_version_dir(self):
        """Returns the path to the directory which is containing the
        migration version files
        """
        return self.__module__ + ':migration_versions'

    def upgrade_database(self, target='head'):
        """Updates the database to a later version of the plugin models.
        Default behaviour is to upgrade to the latest version.
        """
        plugin_dir = current_app.extensions['plugin_manager'].plugin_folder
        plugin_env = os.path.join(plugin_dir, '_migration_environment')
        plugin_rev = "{}@{}".format(self.settings_key, target)
        upgrade(directory=plugin_env, revision=plugin_rev)

    def downgrade_database(self, target='base'):
        """Rolls back the database to a previous version of plugin models.
        Default behaviour is to remove the models completely.
        """
        plugin_dir = current_app.extensions['plugin_manager'].plugin_folder
        plugin_env = os.path.join(plugin_dir, '_migration_environment')
        plugin_rev = "{}@{}".format(self.settings_key, target)
        downgrade(directory=plugin_env, revision=plugin_rev)

    def migrate(self, message=None):
        """Generates new migration files for a plugin and stores them in
        flaskbb/plugins/<plugin_folder>/migration_versions

        :param message: The message of the revision.
        """
        with plugin_name_migrate(self.__module__):
            plugin_dir = current_app.extensions['plugin_manager'].plugin_folder
            plugin_env = os.path.join(plugin_dir, '_migration_environment')
            plugin_ver = os.path.join(self.path, 'migration_versions')
            try:
                migrate(directory=plugin_env, head=self.settings_key)
            except Exception as e:  # presumably this is the initial migration?
                migrate(
                    message=message,
                    directory=plugin_env,
                    version_path=plugin_ver,
                    branch_label=self.settings_key
                )

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
            group = SettingsGroup.query. \
                filter_by(key=self.settings_key). \
                first()
            if group and len(group.settings.all()) > 0:
                return True
            return False
        return False

    def this_version_installed(self):
        installed_migration = Setting.\
            as_dict(self.settings_key).\
            get('version', None)

        if self.uninstallable:
            if installed_migration == self.version:
                return True
            return False
        return None

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
