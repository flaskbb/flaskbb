.. _plugins:

Plugins
=======

.. module:: flaskbb.plugins

FlaskBB provides a full featured plugin system. This system allows you to
easily extend or modify FlaskBB without touching any FlaskBB code. Under the
hood it uses the `pluggy plugin system`_ which does most of the heavy lifting
for us. A list of available plugins can be found at the `GitHub Wiki`_. A
proper index for FlaskBB Plugins and Themes still have to be built.

If you are interested in creating new plugins, checkout out the
:ref:`Developing new Plugins <plugin_development>` page.

.. _`pluggy plugin system`: https://pluggy.readthedocs.io/en/latest/
.. _`GitHub Wiki`: https://github.com/sh4nks/flaskbb/wiki


Management
----------

Before plugins can be used in FlaskBB, they have to be downloaded, installed
and activated.
Plugins can be very minimalistic with nothing to install at all (just enabling
and disabling) to be very complex where you have to `run migrations <./plugins.html#database>`_ and add
some `additional settings <./plugins.html#install>`_.

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

The plugin can be installed via the Admin Panel (in tab 'Plugins') or by
running::

    $ flaskbb plugins install <plugin_name>

This installs the plugin's settings and applies its migrations (if it has
any). To do that for every plugin at once, use ``--all``::

    $ flaskbb plugins install --all

``install``, ``upgrade`` and ``uninstall`` all take care of both halves.
If you only want one of them, restrict the command with ``--settings-only``
or ``--migrations-only``::

    $ flaskbb plugins install <plugin_name> --settings-only
    $ flaskbb plugins install <plugin_name> --migrations-only

.. note:: The Admin Panel only manages the settings of a plugin. Migrations
    are exclusive to the CLI.

Upgrade
~~~~~~~

After updating a plugin to a newer version, its settings and its database
schema might have changed. Both are brought up to date with::

    $ flaskbb plugins upgrade <plugin_name>

or, for every plugin at once::

    $ flaskbb plugins upgrade --all

Uninstall
~~~~~~~~~

Uninstalling a plugin reverts its migrations and wipes its settings from
FlaskBB::

    $ flaskbb plugins uninstall <plugin_name>

Since reverting the migrations drops the plugin's tables, you are asked for
confirmation first. Pass ``--force`` to skip the prompt and ``--all`` to
uninstall every plugin::

    $ flaskbb plugins uninstall --all --force

To keep the plugin's tables around and only get rid of its settings, use
``--settings-only`` - that is also what the Admin Panel does::

    $ flaskbb plugins uninstall <plugin_name> --settings-only

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


Database
--------

Upgrading, downgrading and generating database revisions is all handled
via alembic. We make use of alembic's branching feature to manage seperate
migrations for the plugins. Each plugin will have it's own branch in alembic
where migrations can be managed.

``flaskbb plugins install|upgrade|uninstall`` already run the migrations of
the plugins they act on, so the commands below are only needed if you want
to target a specific revision or are developing a plugin:

* (Auto-)Generating revisions
    ``flaskbb db revision --branch <plugin_name> "<YOUR_MESSAGE>"``

    Replace <YOUR_MESSAGE> with something like "initial migration" if it's
    the first migration or with just a few words that will describe the
    changes of the revision.

* Applying revisions
    ``flaskbb db upgrade <plugin_name>@head``

    If you want to upgrade to specific revision, replace ``head`` with the
    revision id. Without a target, ``flaskbb db upgrade`` upgrades FlaskBB
    and every enabled plugin to their newest revision.

* Downgrading revisions
    ``flaskbb db downgrade <plugin_name>@-1``

    If you just want to revert the latest revision, just use ``-1``.
    To downgrade all database migrations, use ``base``.
