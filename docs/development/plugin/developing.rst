.. _plugin_developing:

Developing new Plugins
======================

If you want to write a plugin, it's a very good idea to checkout existing
plugins. A good starting point for example is the `Portal Plugin`_.

You can scaffold a new plugin from a cookiecutter template with
``flaskbb plugins new`` (see :ref:`the CLI reference <commandline>`) - note
that the default template still generates a ``setup.py``-based layout, so
prefer following the ``pyproject.toml`` layout below (or the `Portal
Plugin`_'s own layout) until the template catches up.

For example, the structure of a plugin could look like this:

.. sourcecode:: text

    your_package_name
    |-- pyproject.toml
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


Setting Up a Development Environment
------------------------------------

You'll need a working FlaskBB development checkout first - see
:doc:`/development/setup` if you don't have one yet. From there, there are
two common ways to get your plugin installed into that environment so
FlaskBB can discover and load it.

Developing a new, standalone plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Scaffold your plugin as its own project (with its own ``pyproject.toml`` -
see `Metadata`_ below), for example as a sibling directory of your FlaskBB
checkout. Then, from FlaskBB's root folder, install it into FlaskBB's own
virtual environment in editable mode::

    $ uv pip install -e ../your-plugin-directory

This uses ``uv``'s pip-compatible interface, which installs straight into
the active ``.venv`` without touching FlaskBB's own ``pyproject.toml`` or
``uv.lock`` - your plugin doesn't need to be a declared dependency of
FlaskBB for this to work. Because it's an editable install, code changes in
your plugin are picked up without reinstalling; just restart ``uv run
flaskbb run`` to pick up backend changes (the dev reloader only watches
FlaskBB's own package by default - pass ``--extra-files`` if you also want
it to restart automatically on your plugin's files).

Since this bypasses the lockfile, a later plain ``uv sync`` will remove it
again as an "extraneous" package - re-run the ``uv pip install -e`` command
above afterwards, or pass ``--inexact`` to ``uv sync`` to keep manually
installed packages around.

Developing the bundled Portal/Conversations plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FlaskBB's own ``pyproject.toml`` already depends on ``flaskbb-plugin-portal``
and ``flaskbb-plugin-conversations`` from PyPI. If you've also checked out
their source, as siblings of FlaskBB (``../flaskbb-plugin-portal`` and
``../flaskbb-plugin-conversations``), swap in editable installs of your
local checkouts with::

    $ make dev-plugins

or directly::

    $ uv pip install -e ../flaskbb-plugin-portal -e ../flaskbb-plugin-conversations

The same caveat as above applies - re-run this after any plain ``uv sync``.

Verifying it's picked up
~~~~~~~~~~~~~~~~~~~~~~~~

Once installed, confirm FlaskBB sees your plugin::

    $ uv run flaskbb plugins list

Then install its settings and, if it ships any, its migrations - see
:ref:`the CLI reference <commandline>` for the full ``flaskbb plugins`` and
``flaskbb db`` command groups::

    $ uv run flaskbb plugins install your_plugin_name

While working on a migration you'll want to apply it directly, without
going through the whole install::

    $ uv run flaskbb db upgrade your_plugin_name@head

Restart the dev server afterwards - plugins are loaded once at startup
(pluggy discovers them via the ``flaskbb_plugins`` entry point), so a
freshly installed or re-enabled plugin only takes effect from the next
process start.


Metadata
--------

FlaskBB Plugins are usually following the naming scheme of
``flaskbb-plugin-YOUR_PLUGIN_NAME`` which should make them better
distinguishable from other PyPI distributions.

A proper plugin should have at least the following metadata in its
``pyproject.toml`` file:

.. sourcecode:: toml

    [project]
    name = "flaskbb-plugin-YOUR_PLUGIN_NAME"  # name on PyPI
    version = "1.0.0"
    description = "<your short description>"
    readme = "README.md"
    license = "<your license>"
    requires-python = ">=3.12"
    authors = [
        {name = "<you>", email = "<your email>"},
    ]
    dependencies = [
        "FlaskBB>=2.2.0",
    ]

    [project.urls]
    Homepage = "<url to your project>"
    Repository = "<url to your repo>"

    [project.entry-points.'flaskbb_plugins']
    unique_name_of_plugin = 'your_package_name'  # most important part

    [build-system]
    requires = ["hatchling"]
    build-backend = "hatchling.build"

    [tool.hatch.build.targets.wheel]
    packages = ["your_package_name"]

The most important part here is ``[project.entry-points.'flaskbb_plugins']``.
Here you tell FlaskBB the unique name of your plugin and where your plugin
module is located inside your project. FlaskBB looks up the
``flaskbb_plugins`` entry point group (via pluggy's
``load_setuptools_entrypoints``) to discover its plugins.

Have a look at the `pyproject.toml specification`_ to get a better idea of
what else can go in there. For a full example, checkout the `Portal
Plugin`_'s own
`pyproject.toml <https://github.com/flaskbb/flaskbb-plugin-portal/blob/master/pyproject.toml>`_.

.. _`pyproject.toml specification`: https://packaging.python.org/en/latest/specifications/pyproject-toml/
.. _`Portal Plugin`: https://github.com/flaskbb/flaskbb-plugin-portal


Settings
--------
Plugins can create settings which integrate with the 'Plugin Settings'
section of the Admin Panel.

Settings are declared as a
:class:`~flaskbb.core.settings.definitions.SettingGroup` of
:class:`~flaskbb.core.settings.definitions.SettingDefinition` instances
(``StringSetting``, ``IntSetting``, ``BoolSetting``, ``SelectSetting``,
``SelectMultipleSetting``) and registered by implementing the
``flaskbb_load_setting_groups`` hook. The group's ``key`` must be unique
across FlaskBB **and** must equal your plugin's entry point name - that's
how FlaskBB's ``PluginRegistry`` finds "its" settings when installing,
upgrading or uninstalling the plugin.

::

    from flaskbb.core.settings import IntSetting, SelectMultipleSetting, SettingGroup
    from pluggy import HookimplMarker

    impl = HookimplMarker("flaskbb")

    SETTINGS = SettingGroup(
        # Has to match the plugin's entry point name.
        key="portal",

        name="Portal Settings",
        description="Portal settings for your FlaskBB forum.",

        settings=(
            SelectMultipleSetting(
                # Only has to be unique within this group.
                key="FORUM_IDS",

                # Default value. The type depends on the definition class.
                value=[1],

                # The human readable name of your configuration variable.
                name="Forums",

                # A short description of what the setting does.
                description=("The forum ids from which forums the posts "
                             "should be displayed on the portal."),

                # SelectSetting/SelectMultipleSetting-only: a callable
                # returning (value, label) pairs, and an optional coerce
                # type for the selected value(s).
                choices=available_forums,
                coerce=int,
            ),
            IntSetting(
                key="RECENT_TOPICS",
                value=10,
                min=1,
                name="Number of Recent Topics",
                description="The number of topics in Recent Topics.",
            ),
        ),
    )

    @impl
    def flaskbb_load_setting_groups():
        return SETTINGS

.. currentmodule:: flaskbb.core.settings.definitions

.. table:: Available Setting Definitions
    :widths: auto

    ======================================== =================
    Definition                                Parsed & Saved As
    ======================================== =================
    :class:`StringSetting`                    :class:`str`
    :class:`IntSetting`                       :class:`int`
    :class:`BoolSetting`                      :class:`bool`
    :class:`SelectSetting`                    single value
    :class:`SelectMultipleSetting`            :class:`list`
    ======================================== =================

.. table:: Available Additional Options

    =========== ====================== ========================================
    Options     Applicable Types       Description
    =========== ====================== ========================================
    ``min``     string, integer        **Optional.** The minimum required
                                       length of the setting value. If used on
                                       a numeric type, it will check the
                                       minimum value.
    ``max``     string, integer        **Optional.** The maximum required
                                       length of the setting value. If used on
                                       a numeric type, it will check the
                                       maximum value.
    ``choices`` select, selectmultiple **Required.** A callable which returns
                                       a sequence of (value, label) pairs.
    ``coerce``  select, selectmultiple **Optional.** Coerces the selected
                                       value(s) to the given type. Defaults to
                                       ``str``.
    =========== ====================== ========================================

Once registered, your plugin's settings are exposed prefixed with the
group's key, e.g. ``PORTAL_FORUM_IDS``, to avoid colliding with core
settings or another plugin's - accessible at runtime via
``flaskbb_config.PORTAL_FORUM_IDS``.

For more information see the :ref:`settings` chapter.

