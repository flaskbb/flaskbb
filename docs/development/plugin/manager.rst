.. _plugin_management:


Plugin Management
=================

FlaskBB provides a couple of helpers for helping with plugin management.


Plugin Registry
---------------
The plugin registry holds all available plugins. It shows the plugin's status
whether it is enabled or disabled, installable or installed. The registry also
holds a reference to the plugin's instance, provides an interface to access
the plugins metadata and stores its settings.

You can query it like any SQLAlchemy Model::

    plugin = PluginRegistry.query.filter_by(name="portal").first()


.. autoclass:: flaskbb.plugins.models.PluginRegistry
    :members:


Plugin Manager
--------------
FlaskBB overrides the PluginManager from pluggy to provide some additional
functionality like accessing the information stored in a setup.py file. The
plugin manager will only list the currently enabled plugins and can be used to
directly access the plugins instance by its name.


Accessing a plugins instance is as easy as::

    plugin_instance = current_app.pluggy.get_plugin(name)


.. autoclass:: flaskbb.plugins.manager.FlaskBBPluginManager
    :members:
    :inherited-members:
