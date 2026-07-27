.. _plugin_translations:

Translating Plugins
====================

Plugins ship and are translated exactly like core FlaskBB (see
:ref:`localization` for the general workflow) — a plugin just owns its own
``translations/`` directory and registers it with FlaskBB instead of relying
on the core one.

Registering translations
-------------------------

A plugin points FlaskBB at its translation directory by implementing the
:func:`flaskbb_load_translations
<flaskbb.plugins.spec.flaskbb_load_translations>` hook and returning the
absolute path to it:

.. code-block:: python

    import os

    from pluggy import HookimplMarker

    hookimpl = HookimplMarker("flaskbb")


    @hookimpl
    def flaskbb_load_translations():
        return os.path.join(os.path.dirname(__file__), "translations")

``FlaskBBDomain`` merges every plugin's translations into whichever locale
is active for the request, so plugin strings and core strings can be used
side by side in the same template.

Marking strings for translation follows the same rules as core: wrap
user-facing strings in ``gettext``/``lazy_gettext`` in Python and use
``_()`` in Jinja templates. Add a ``babel.cfg`` at the plugin's project root
so ``pybabel`` knows which files to scan, e.g. (from the Portal plugin):

.. sourcecode:: ini

    [ignore: .tox/**]
    [ignore: .venv/**]
    [python: **/portal/**.py]
    [jinja2: **/templates/**.html]

Directory layout
----------------

A plugin's translations live under its own package, one directory per
language code, same as core:

.. sourcecode:: text

    your_package_name
    |-- your_package_name
        |-- translations
            |-- messages.pot
            |-- de
            |   |-- LC_MESSAGES
            |       |-- messages.po
            |       |-- messages.mo
            |-- en
                |-- LC_MESSAGES
                    |-- messages.po
                    |-- messages.mo

Updating and compiling
-----------------------

If the plugin is installed into the same environment you're running
FlaskBB from, use the ``flaskbb translations`` CLI's ``--plugin`` option,
passing the plugin's *entry point name* (the name registered under the
``flaskbb_plugins`` entry point group in ``pyproject.toml``/``setup.py`` —
e.g. ``portal``, not the ``flaskbb-plugin-portal`` distribution name):

.. sourcecode:: console

    flaskbb translations new de --plugin portal
    flaskbb translations update --plugin portal
    flaskbb translations compile --plugin portal

``flaskbb translations update --all`` and ``flaskbb translations compile
--all`` do the same for every installed plugin at once, in addition to
core.

Working from inside the plugin's own repo (without going through FlaskBB's
CLI) is just calling ``pybabel`` directly against the plugin's own
``babel.cfg`` and ``translations/`` directory, e.g.:

.. sourcecode:: console

    pybabel extract -F babel.cfg -k lazy_gettext -o your_package/translations/messages.pot .
    pybabel update -i your_package/translations/messages.pot -d your_package/translations/
    pybabel compile -d your_package/translations/

    # first time only, per language:
    pybabel init -i your_package/translations/messages.pot -d your_package/translations/ -l LANG

This is the approach the Portal and Conversations plugins use in their own
``Makefile`` (``make update-translations`` / ``make add-translation`` /
``make compile-translations``), since a plugin repo doesn't have FlaskBB's
CLI installed as an app.

.. note::
    Whichever path you use, don't forget to compile after updating — Flask-
    BabelPlus loads the binary ``.mo`` files, not the human-edited ``.po``
    source, so an update without a compile step won't show up in the app.
