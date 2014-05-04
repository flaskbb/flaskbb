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

    def enable(self):
        hooks.add("beforeIndex", hello_world)

    def disable(self):
        hooks.remove("beforeIndex", hello_world)

    def install(self):
        pass

    def uninstall(self):
        pass
