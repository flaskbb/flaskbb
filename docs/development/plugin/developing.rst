.. _plugin_developing:

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

For more information see the :ref:`settings` chapter.

