.. _plugins:

Plugins
=======

.. module:: flaskbb.plugins

FlaskBB provides a full featured plugin system. This system allows you to
easily extend or modify FlaskBB without touching any FlaskBB code. Under the
hood it uses the `pluggy plugin system`_ which does most of the heavy lifting
for us.

.. _`pluggy plugin system`: https://pluggy.readthedocs.io/en/latest/

Structure
---------

A plugin has it's own folder where all the plugin specific files are living.
For example, the structure of a plugin could look like this

.. sourcecode:: text

    my_plugin_package
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
~~~~~~~~

A proper plugin should have at least put the following metadata into
the ``setup.py`` file.

.. sourcecode:: python

    setup(
        name="myproject",
        version='1.0',
        url=<url to your project>,
        license=<your license>,
        author=<you>,
        author_email=<your email>,
        description=<your short description>,
        long_description=__doc__,
        packages=find_packages('.'),
        include_package_data=True,
        zip_safe=False,
        platforms='any',

        entry_points={
            'flaskbb_plugin': [
                'unique_name_of_plugin = myproject.pluginmodule',  # most important part
            ]
        }
    )


The most important part is the ``entry_point``. Here you tell FlaskBB the
unique name of your plugin and where your plugin module is located inside
your project. Entry points are a feature that is provided by setuptools.
FlaskBB looks up the ``flaskbb_plugin`` entrypoint to discover its plugins.

Have a look at the `setup script`_ documentation and the `sample setup.py`_
file to get a better idea what the ``setup.py`` file is all about it.

To get a better idea how a plugin looks like, checkout the `Portal Plugin`_.

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


Database
--------

Upgrading, downgrading and generating database revisions is all handled
via alembic. We make use of alembic's branching feature to manage seperate
migrations for the plugins. Each plugin will have it's own branch in alembic
where migrations can be managed. Following commands are used for generaring,
upgrading and downgrading your plugins database migrations:

* (Auto-)Generating revisions
    ``flaskbb db revision --branch <plugin_name> "<YOUR_MESSAGE>"``

    Replace <YOUR_MESSAGE> with something like "initial migration" if it's
    the first migration or with just a few words that will describe the
    changes of the revision.

* Applying revisions
    ``flaskbb db upgrade <plugin_name>@head``

    If you want to upgrade to specific revision, replace ``head`` with the
    revision id.

* Downgrading revisions
    ``flaskbb db downgrade <plugin_name>@-1``

    If you just want to revert the latest revision, just use ``-1``.
    To downgrade all database migrations, use ``base``.


Management
----------

Before plugins can be used in FlaskBB, they have to be downloaded, installed
and activated.
Plugins can be very minimalistic with nothing to install at all (just enabling
and disabling) to be very complex where you have to run migrations and add
some additional settings.

Download
~~~~~~~~

Downloading a Plugin is as easy as::

    $ pip install flaskbb-plugin-MYPLUGIN

if the plugin has been uploaded to PyPI. If you haven't uploaded your plugin
to PyPI or are in the middle of developing one, you can just::

    $ pip install -e .

in your plugin's package directory to install it.

Remove
~~~~~~

Removing a plugin is a little bit more tricky. By default, FlaskBB does not
remove the settings of a plugin by itself because this could lead to some
unwanted dataloss.

`Disable`_ and `Uninstall`_ the plugin first before continuing.

After taking care of this and you are confident that you won't need the
plugin anymore you can finally remove it::

    $ pip uninstall flaskbb-plugin-MYPLUGIN

There is a setting in FlaskBB which lets you control the deletion of settings
of a plugin. If ``REMOVE_DEAD_PLUGINS`` is set to ``True``, all not available
plugins (not available on the filesystem) are constantly removed. Only change
this if you know what you are doing.

Install
~~~~~~~

In our context, by installing a plugin, we mean, to install the settings
and apply the migrations. Personal Note: I can't think of a better name and
I am open for suggestions.

The migrations have to be applied this way (if any, check the plugins docs)::

    flaskbb db upgrade <plugin_name>@head

The plugin can be installed via the Admin Panel (in tab 'Plugins') or by
running::

    flaskbb plugins install <plugin_name>

Uninstall
~~~~~~~~~

Removing a plugin involves two steps. The first one is to check if the plugin
has applied any migrations on FlaskBB and if so you can
undo them via::

    $ flaskbb db downgrade <plugin_name>@base

The second step is to wipe the settings from FlaskBB which can be done in the
Admin Panel or by running::

    $ flaskbb plugins uninstall <plugin_name>

Disable
~~~~~~~

Disabling a plugin has the benefit of keeping all the data of the plugin but
not using the functionality it provides. A plugin can either be deactivated
via the Admin Panel or by running::

    flaskbb plugins disable <plugin_name>

.. important:: Restart the server.

    You must restart the wsgi/in-built server in order to make the changes
    effect your forum.


Enable
~~~~~~

All plugins are activated by default. To activate a deactivated plugin you
either have to activate it via the Admin Panel again or by running the
activation command::

    flaskbb plugins enable <plugin_name>


Hooks
-----
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
