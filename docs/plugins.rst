.. _plugins:

Plugins
=======

.. module:: flaskbb.plugins

FlaskBB provides an easy way to extend the functionality of your forum
via so called `Plugins`. Plugins do not modify the `core` of FlaskBB, so
you can easily activate and deactivate them anytime. This part of the
documentation only covers the basic things for creating plugins. If you are
looking for a tutorial you need to go to this section of the documentation:
:doc:`plugin_tutorial/index`.


Structure
---------

A plugin has it's own folder where all the plugin specific files are living.
For example, the structure of a plugin could look like this

.. sourcecode:: text

    my_plugin
    |-- info.json                Contains the Plugin's metadata
    |-- license.txt              The full license text of your plugin
    |-- __init__.py              The plugin's main class is located here
    |-- views.py
    |-- models.py
    |-- forms.py
    |-- static
    |   |-- style.css
    |-- templates
        |-- myplugin.html
    |-- migrations
        |-- 59f7c49b6289_init.py

Management
----------

Database
~~~~~~~~

Upgrading, downgrading and generating database revisions is all handled
via alembic. We make use of a alembic feature called 'branch_labels'.
Each plugin's identifier will be used as a branch_label if used with alembic.
Lets say, that identifier of your plugin is ``portal_plugin``, then you have
to use the following commands for generaring, upgrading and downgrading
your plugins database migrations:

* (Auto-)Generating revisions
    ``flaskbb db revision --branch portal_plugin "<YOUR_MESSAGE>"``

    Replace <YOUR_MESSAGE> with something like "initial migration" if it's
    the first migration or with just a few words that will describe the
    changes of the revision.

* Applying revisions
    ``flaskbb db upgrade portal_plugin@head``

    If you want to upgrade to specific revision, replace ``head`` with the
    revision id.

* Downgrading revisions
    ``flaskbb db downgrade portal_plugin@-1``

    If you just want to revert the latest revision, just use ``-1``.
    To downgrade all database migrations, use ``base``.


Deactivating
~~~~~~~~~~~~

The only way to disable a plugin without removing it is, to add a ``DISABLED``
file in the plugin's root folder. You need to reload your application in order
to have the plugin fully disabled. A disabled plugin could look like this::

    my_plugin
    |-- DISABLED    # Just add a empty file named "DISABLED" to disable a plugin
    |-- info.json
    |-- __init__.py

.. important:: Restart the server.

    You must restart the wsgi/in-built server in order to make the changes
    effect your forum.


Activating
~~~~~~~~~~

Simply remove the ``DISABLED`` file in the plugin directory and restart the
server.


Example Plugin
--------------

A simple Plugin could look like this:

.. sourcecode:: python

    from flask import flash
    from flask.ext.plugins import connect_event

    from flaskbb.plugins import FlaskBBPlugin


    # This is the name of your Plugin class which implements FlaskBBPlugin.
    # The exact name is needed in order to be recognized as a plugin.
    __plugin__ "HelloWorldPlugin"


    def flash_index():
        """Flashes a message when visiting the index page."""

        flash("This is just a demonstration plugin", "success")


    class HelloWorldPlugin(FlaskBBPlugin):
        def setup(self):
            connect_event(before-forum-index-rendered, flash_index)

        def install(self):
            # there is nothing to install
            pass

        def uninstall(self):
            # and nothing to uninstall
            pass


Your plugins also needs a ``info.json`` file, where it stores some meta data
about the plugin. For more information see the `Metadata <#metadata>`_
section below.


Metadata
~~~~~~~~

In order to get a working plugin, following metadata should be defined
in a ``info.json`` file.

``identifier`` : **required**
    The plugin's identifier. It should be a Python identifier (starts with a
    letter or underscore, the rest can be letters, underscores, or numbers)
    and should match the name of the plugin's folder.

``name`` : **required**
    A human-readable name for the plugin.

``author`` : **required**
    The name of the plugin's author, that is, you. It does not have to include
    an e-mail address, and should be displayed verbatim.

``description``
    A description of the plugin in a few sentences. If you can write multiple
    languages, you can include additional fields in the form
    ``description_lc``, where ``lc`` is a two-letter language code like ``es``
    or ``de``. They should contain the description, but in the indicated
    language.

``website``
    The URL of the plugin's Web site. This can be a Web site specifically for
    this plugin, Web site for a collection of plugins that includes this plugin,
    or just the author's Web site.

``license``
    A simple phrase indicating your plugin's license, like ``GPL``,
    ``MIT/X11``, ``Public Domain``, or ``Creative Commons BY-SA 3.0``. You
    can put the full license's text in the ``license.txt`` file.

``version``
    This is simply to make it easier to distinguish between what version
    of your plugin people are using. It's up to the theme/layout to decide
    whether or not to show this, though.


Events
------

A full list with events can be found here :doc:`events`.


Plugin Class
------------

.. autoclass:: FlaskBBPlugin

  .. autoattribute:: settings_key

  .. autoattribute:: has_settings

  .. autoattribute:: installed

  .. automethod:: setup

  .. automethod:: install

  .. automethod:: uninstall

  .. automethod:: register_blueprint
