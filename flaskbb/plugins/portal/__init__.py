from flaskbb.extensions import db
from flaskbb.plugins import Plugin

from .portal import PortalModel


#: The name of your plugin class
__plugin__ = "PortalPlugin"


class PortalPlugin(Plugin):
    models = [PortalModel]

    name = "Portal Plugin"
    description = "A simple Portal"

    def install(self):
        self.create_all_tables(db)
        #
        # register hooks and blueprints/routes here

    def uninstall(self):
        self.drop_all_tables(db)
