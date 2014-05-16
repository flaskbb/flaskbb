from flask.ext.plugins import connect_event

from flaskbb.plugins import FlaskBBPlugin
from .views import portal, inject_portal_link

__version__ = "0.1"
__plugin__ = "PortalPlugin"


class PortalPlugin(FlaskBBPlugin):

    name = "Portal Plugin"

    description = ("This Plugin provides a simple portal for FlaskBB.")

    author = "sh4nks"

    license = "BSD"

    version = __version__

    def setup(self):
        self.register_blueprint(portal, url_prefix="/portal")
        connect_event("before-first-navigation-element", inject_portal_link)
