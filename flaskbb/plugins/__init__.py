from flask.ext.plugins import Plugin
from flask import current_app

from flaskbb.admin.models import SettingsGroup


class FlaskBBPlugin(Plugin):

    #: This is the :class:`SettingsGroup` key - if your the plugin needs to install
    #: additional things you must set it, else it won't install anything.
    settings_key = None

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
            group = SettingsGroup.query.filter_by(key=self.settings_key).first()
            if group and len(group.settings.all()) > 0:
                return True
            return False
        return False

        # Some helpers
    def register_blueprint(self, blueprint, **kwargs):
        """Registers a blueprint."""
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
