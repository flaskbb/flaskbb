from flask import flash
from flaskbb.plugins import Plugin, hooks


#: The name of your plugin class
__plugin__ = "ExamplePlugin"


def hello_world():
    flash("Hello World from {}".format(__plugin__), "success")


class ExamplePlugin(Plugin):
    @property
    def description(self):
        return "Example plugin"

    @property
    def version(self):
        return "1.0.0"

    def install(self):
        # register hooks and blueprints/routes here
        hooks.registered.beforeIndex.append(hello_world)

    def uninstall(self):
        pass
