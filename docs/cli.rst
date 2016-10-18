.. _commandline:

Command Line Interface
======================

Here you find the documentation about FlaskBB's Command Line Interface.
The command line is provided by click.

To get help for a commands, just type ``flaskbb COMMAND --help``.
If no command options or arguments are used it will print out all
available commands

.. sourcecode:: text

    Usage: flaskbb [OPTIONS] COMMAND [ARGS]...

      This is the commandline interface for flaskbb.

    Options:
      --help  Show this message and exit.

    Commands:
      db            Perform database migrations.
      install       Interactively setup flaskbb.
      plugins       Plugins command sub group.
      populate      Creates the database with some test data.
      run           Runs a development server.
      setup         Runs a preconfigured setup for FlaskBB.
      shell         Runs a shell in the app context.
      start         Starts a production ready wsgi server.
      themes        Themes command sub group.
      translations  Translations command sub group.
      upgrade       Updates the migrations and fixtures.
      users         Create, update or delete users.



Commands
--------

You can find a complete overview, including the ones from the sub groups,
below.


.. program:: flaskbb


.. option:: install

        Installs flaskbb. If no arguments are used, an interactive setup
        will be run.


.. option:: upgrade

    Updates the migrations and fixtures to the latest version.

    .. option:: --all, -a

        Upgrades migrations AND fixtures to the latest version.

    .. option:: --fixture FIXTURE, -f FIXTURE

        The fixture which should be upgraded or installed.
        All fixtures have to be places inside flaskbb/fixtures/

    .. option:: --force-fixture, -ff

        Forcefully upgrades the fixtures. WARNING: This will also overwrite
        any settings.


.. option:: populate

        Creates the necessary tables and groups for FlaskBB.

        .. option:: --test, -t

            Adds some test data.

        .. option:: --posts

            Number of posts to create in each topic (default: 100).

        .. option:: --topics

            Number of topics to create (default: 100).

        .. option:: --force, -f

            Will delete the database before populating it.


.. option:: runserver

        Starts the development server


.. option:: start

    Starts a production ready wsgi server.
    TODO: Unsure about this command, would 'serve' or 'server' be better?

    .. option:: --server SERVER

        Defaults to gunicorn. The following WSGI Servers are supported:
            - gunicorn (default)
            - TODO


.. option:: shell

    Creates a python shell with an app context.


.. option:: translations

    Translations command sub group.

    .. option:: add LANGUAGE_CODE

        Adds a new language to FlaskBB's translations.
        The ``LANGUAGE_CODE`` is the short identifier for the language i.e.
        '``en``', '``de``', '``de_AT``', etc.

        .. option:: -p, --plugin PLUGIN_NAME

            Adds a new language to a plugin.

    .. option:: update

        Updates all translations, including the ones from the plugins.
        Use -p <PLUGIN_NAME> to only update the translation of a given
        plugin.

        .. option:: -p, --plugin PLUGIN_NAME

            Update the language of the given plugin.

    .. option:: compile

        Compiles all translations, including the ones from the plugins.

        .. option:: -p, --plugin PLUGIN_NAME

            Compiles only the given plugin translation.


.. option:: plugins

    Plugins command sub group.

    .. option:: create PLUGIN_NAME

        Creates a basic starter template for a new plugin.

    .. option:: add PLUGIN_NAME

        Adds a new plugin.

    .. option:: remove PLUGIN_NAME

        Removes a plugin.


.. option:: themes

    Themes command sub group.

    .. option:: create THEME_NAME

        Creates a basic starter template for a new theme.

    .. option:: add THEME_NAME

        Adds a new theme.

    .. option:: remove THEME_NAME

        Removes a theme.


.. option:: users

    Creates a new user. Pass any arguments to omit the interactive mode.

    .. option:: -g, --group GROUP

        Uses ``GROUP`` as the primary group.

    .. option:: -u, --username USERNAME

        Uses ``USERNAME`` as the name of the new user.

    .. option:: -p, --password PASSWORD

        Uses ``PASSWORD`` as password for the new user. But you have to ḱnow,
        that when choosing this option, the password is most likely stored
        in a history file (i.e. ``.bash_history``).

    .. option:: -e, --email EMAIL

        Uses ``EMAIL`` as the email address for the new user.
