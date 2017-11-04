.. _plugin_development:


Developing new Plugins
======================

If you want to write a plugin, it's a very good idea to checkout existing
plugins. A good starting point for example is the `Portal Plugin`_.

Also make sure to check out the cookiecutter-flaskbb-plugin project, which is a
cookiecutter template which helps you to create new plugins.

For example, the structure of a plugin could look like this:

.. sourcecode:: text

    your_package_name
    |-- setup.py
    |-- my_plugin
        |-- __init__.py
        |-- views.py
        |-- models.py
        |-- forms.py
        |-- static
        |   |-- style.css
        |-- templates
            |-- myplugin.html
        |-- migrations
            |-- 59f7c49b6289_init.py

Metadata
--------

FlaskBB Plugins are usually following the naming scheme of
``flaskbb-plugin-YOUR_PLUGIN_NAME`` which should make them better
distinguishable from other PyPI distributions.

A proper plugin should have at least put the following metadata into
the ``setup.py`` file.

.. sourcecode:: python

    setup(
        name="flaskbb-plugin-YOUR_PLUGIN_NAME",  # name on PyPI
        packages=["your_package_name"],  # name of the folder your plugin is located in
        version='1.0',
        url=<url to your project>,
        license=<your license>,
        author=<you>,
        author_email=<your email>,
        description=<your short description>,
        long_description=__doc__,
        include_package_data=True,
        zip_safe=False,
        platforms='any',

        entry_points={
            'flaskbb_plugin': [
                'unique_name_of_plugin = your_package_name.pluginmodule',  # most important part
            ]
        }
    )

The most important part here is the ``entry_point``. Here you tell FlaskBB the
unique name of your plugin and where your plugin module is located inside
your project. Entry points are a feature that is provided by setuptools.
FlaskBB looks up the ``flaskbb_plugin`` entrypoint to discover its plugins.
Have a look at the `setup script`_ documentation and the `sample setup.py`_
file to get a better idea what the ``setup.py`` file is all about it.

For a full example, checkout the `Portal Plugin`_.

.. _`setup script`: https://docs.python.org/3.6/distutils/setupscript.html#additional-meta-data
.. _`sample setup.py`: https://github.com/pypa/sampleproject/blob/master/setup.py
.. _`Portal Plugin`: https://github.com/sh4nks/flaskbb-plugins/tree/master/portal


Settings
--------
Plugins can create settings which integrate with the 'Settings' tab of
the Admin Panel.

The settings are stored in a dictionary with a given structure. The name of
the dictionary must be ``SETTINGS`` and be placed in the plugin module.

The structure of the ``SETTINGS`` dictionary is best explained via an
example::

    SETTINGS = {
        # This key has to be unique across FlaskBB.
        # Using a prefix is recommended.
        'forum_ids': {

            # Default Value. The type of the default value depends on the
            # SettingValueType.
            'value': [1],

            # The Setting Value Type.
            'value_type': SettingValueType.selectmultiple,

            # The human readable name of your configuration variable
            'name': "Forum IDs",

            # A short description of what the settings variable does
            'description': ("The forum ids from which forums the posts "
                            "should be displayed on the portal."),

            # extra stuff like the 'choices' in a select field or the
            # validators are defined in here
            'extra': {"choices": available_forums, "coerce": int}
        }
    }

.. currentmodule:: flaskbb.utils.forms

.. table:: Available Setting Value Types
    :widths: auto

    ======================================== =================
    Setting Value Type                       Parsed & Saved As
    ======================================== =================
    :attr:`SettingValueType.string`          :class:`str`
    :attr:`SettingValueType.integer`         :class:`int`
    :attr:`SettingValueType.float`           :class:`float`
    :attr:`SettingValueType.boolean`         :class:`bool`
    :attr:`SettingValueType.select`          :class:`list`
    :attr:`SettingValueType.selectmultiple`  :class:`list`
    ======================================== =================

.. table:: Available Additional Options via the ``extra`` Keyword

    =========== ====================== ========================================
    Options     Applicable Types       Description
    =========== ====================== ========================================
    ``min``     string, integer, float **Optional.** The minimum required
                                       length of the setting value. If used on
                                       a numeric type, it will check the
                                       minimum value.
    ``max``     string, integer, float **Optional.** The maximum required
                                       length of the setting value. If used on
                                       a numeric type, it will check the
                                       maximum value.
    ``choices`` select, selectmultiple **Required.** A callable which returns
                                       a sequence of (value, label) pairs.
    ``coerce``  select, selectmultiple **Optional.** Coerces the select values
                                       to the given type.
    =========== ====================== ========================================


Validating the size of the integer/float and the length of the string fields
is also possible via the ``min`` and ``max`` keywords::

    'recent_topics': {
        ...
        'extra': {"min": 1},
    },

The ``select`` and ``selectmultiple`` fields have to provide a callback which
lists all the available choices. This is done via the ``choices`` keyword.
In addition to that they can also specify the ``coerce`` keyword which will
coerce the input value into the specified type.::

    'forum_ids': {
        ...
        'extra': {"choices": available_forums, "coerce": int}
    }

For more information see the :doc:`settings` chapter.


Using Hooks
-----------
Hooks are invoked based on an event occurring within FlaskBB. This makes it
possible to change the behavior of certain actions without modifying the
actual source code of FlaskBB.

For your plugin to actually do something useful, you probably want to 'hook'
your code into FlaskBB. This can be done throughout a lot of places in the
code. FlaskBB loads and calls the hook calls hook functions from registered
plugins for any given hook specification.

Each hook specification has a corresponding hook implementation. By default,
all hooks that are prefix with ``flaskbb_`` will be marked as a standard
hook implementation. It is possible to modify the behavior of hooks.
For example, default hooks are called in LIFO registered order.
A hookimpl can influence its call-time invocation position using special
attributes. If marked with a "tryfirst" or "trylast" option it will be executed
first or last respectively in the hook call loop::

    hookimpl = HookimplMarker('flaskbb')

    @hookimpl(trylast=True)
    def flaskbb_additional_setup(app):
        return "save the best for last"


In order to extend FlaskBB with your Plugin you will need to connect your
callbacks to the hooks.

Let's look at an actually piece of `used code`_.

.. sourcecode:: python

    def flaskbb_load_blueprints(app):
        app.register_blueprint(portal, url_prefix="/portal")

By defining a function called ``flaskbb_load_blueprints``, which has a
corresponding hook specification under the same name. FlaskBB will pass
in an ``app`` object as specified in the hook spec, which we will use to
register a new blueprint. It is also possible to completely omit the ``app``
argument from the function where it is **not possible** to add new arguments to
the hook implemention.

For a complete list of all available hooks in FlaskBB see the :doc:`hooks`
section.

pytest and pluggy are good resources to get better understanding on how to
write `hook functions`_ using `pluggy`_.

.. _`used code`: https://github.com/sh4nks/flaskbb-plugins/blob/master/portal/portal/__init__.py#L31
.. _`hook functions`: https://docs.pytest.org/en/latest/writing_plugins.html#writing-hook-functions
.. _`pluggy`: https://pluggy.readthedocs.io/en/latest/#defining-and-collecting-hooks


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
FlaskBB overrides the PluginManager from pluggy to provide some additional functionality like accessing the information stored in a setup.py file. The plugin manager will only list the currently enabled plugins and can be used to directly access the plugins instance by its name.


Accessing a plugins instance is as easy as::

    plugin_instance = current_app.pluggy.get_plugin(name)


.. autoclass:: flaskbb.plugins.manager.FlaskBBPluginManager
    :members:
    :inherited-members:
