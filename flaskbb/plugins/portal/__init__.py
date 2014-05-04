from flask import current_app
from flaskbb.extensions import db
from flaskbb.plugins import Plugin

from .portal import PortalModel, portal


#: The name of your plugin class
__plugin__ = "PortalPlugin"


class PortalPlugin(Plugin):
    # Register the models
    models = [PortalModel]

    @property
    def name(self):
        return "Portal Plugin"

    @property
    def description(self):
        return "A simple portal plugin"

    @property
    def version(self):
        return "0.0.1"

    def enable(self):
        pass

    def disable(self):
        pass

    def install(self):
        self.create_all_tables(db)
        current_app.register_blueprint(portal)
        # register hooks and blueprints/routes here

    def uninstall(self):
        self.drop_all_tables(db)
