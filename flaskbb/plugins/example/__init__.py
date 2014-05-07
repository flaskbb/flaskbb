from flask import flash
from flask.ext.plugins import Plugin

from flaskbb.hooks import hooks

#: The name of your plugin class
__version__ = "1.0.0"
__plugin__ = "ExamplePlugin"


def hello_world():
    flash("Hello World from {}".format(__plugin__), "success")


def inject_hello_world():
    return "<b>Hello World</b>"


class ExamplePlugin(Plugin):

    name = "Example Plugin"

    description = ("This plugin gives a quick insight on how you can write "
                   "plugins in FlaskBB.")

    author = "sh4nks"

    license = "BSD License. See LICENSE file for more information."

    version = __version__

    def enable(self):
        hooks.add("beforeIndex", hello_world)
        hooks.add("beforeBreadcrumb", inject_hello_world)

    def disable(self):
        hooks.remove("beforeIndex", hello_world)
        hooks.remove("beforeBreadcrumb", inject_hello_world)

    def install(self):
        pass

    def uninstall(self):
        pass
