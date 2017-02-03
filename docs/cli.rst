.. _commandline:

Command Line Interface
======================

Here you can find the documentation about FlaskBB's Command Line Interface.

To get help for a commands, just type ``flaskbb COMMAND --help``.
If no command options or arguments are used it will display all available
commands.

.. sourcecode:: text

    Usage: flaskbb [OPTIONS] COMMAND [ARGS]...

      This is the commandline interface for flaskbb.

    Options:
      --config CONFIG  Specify the config to use in dotted module notation e.g.
                       flaskbb.configs.default.DefaultConfig
      --version        Show the FlaskBB version.
      --help           Show this message and exit.

    Commands:
      celery           Preconfigured wrapper around the 'celery' command.
      db               Perform database migrations.
      download-emojis  Downloads emojis from emoji-cheat-sheet.com.
      install          Installs flaskbb.
      makeconfig       Generates a FlaskBB configuration file.
      plugins          Plugins command sub group.
      populate         Creates the necessary tables and groups for FlaskBB.
      reindex          Reindexes the search index.
      run              Runs a development server.
      shell            Runs a shell in the app context.
      start            Starts a production ready wsgi server.
      themes           Themes command sub group.
      translations     Translations command sub group.
      upgrade          Updates the migrations and fixtures.
      urls             Show routes for the app.
      users            Create, update or delete users.


Commands
--------

Here you will find a detailed description of every command including all
of their options and arguments.

.. I am cheating here as i don't know how else to get rid of the warnings

.. describe:: flaskbb install

    Installs flaskbb. If no arguments are used, an interactive setup
    will be run.

    .. describe:: --welcome, -w

        Disables the generation of the welcome forum.

    .. describe:: --force, -f

        Doesn't ask for confirmation if the database should be deleted or not.

    .. describe:: --username USERNAME, -u USERNAME

        The username of the user.

    .. describe:: --email EMAIL, -e EMAIL

        The email address of the user.

    .. describe:: --password PASSWORD, -p PASSWORD

        The password of the user.

    .. describe:: --group GROUP, -g GROUP

        The primary group of the user. The group ``GROUP`` has to be
        one of ``admin``, ``super_mod``, ``mod`` or ``member``.

.. describe:: flaskbb upgrade

    Updates the migrations and fixtures.

    .. describe:: --all, -a

        Upgrades migrations AND fixtures to the latest version.

    .. describe:: --fixture FIXTURE, -f FIXTURE

        The fixture which should be upgraded or installed.
        All fixtures have to be places inside flaskbb/fixtures/

    .. describe:: --force-fixture, -ff

        Forcefully upgrades the fixtures. WARNING: This will also overwrite
        any settings.

.. describe:: flaskbb populate

    Creates the necessary tables and groups for FlaskBB.

    .. describe:: --test-data, -t

        Adds some test data.

    .. describe:: --bulk-data, -b

        Adds a lot of test data. Has to be used in combination with
        ``--posts`` and ``--topics``.

    .. describe:: --posts

        Number of posts to create in each topic (default: 100).

    .. describe:: --topics

        Number of topics to create (default: 100).

    .. describe:: --force, -f

        Will delete the database without asking before populating it.

    .. describe:: --initdb, -i

        Initializes the database before populating it.

.. describe:: flaskbb runserver

    Starts the development server

.. describe:: flaskbb start

    Starts a production ready wsgi server.
    Other versions of starting FlaskBB are still supported!

    .. describe:: --server SERVER, -s SERVER

        Defaults to ``gunicorn``. The following WSGI Servers are supported:
            - gunicorn (default)
            - gevent

    .. describe:: --host HOST, -h HOST

        The interface to bind FlaskBB to. Defaults to ``127.0.0.1``.

    .. describe:: --port PORT, -p PORT

        The port to bind FlaskBB to. Defaults to ``8000``.

    .. describe:: --workers WORKERS, -w WORKERS

        The number of worker processes for handling requests.
        Defaults to ``4``.

    .. describe:: --daemon, -d

        Starts gunicorn in daemon mode.

    .. describe:: --config, -c

        The configuration file to use for the FlaskBB WSGI Application.

.. describe:: flaskbb celery CELERY_ARGS

    Starts celery. This is just a preconfigured wrapper around the ``celery``
    command. Additional arguments are directly passed to celery.

    .. describe:: --help-celery

        Shows the celery help message.

.. describe:: flaskbb shell

    Creates a python shell with an app context.

.. describe:: flaskbb urls

    Lists all available routes.

    .. describe:: --route, -r

        Order by route.

    .. describe:: --endpoint, -e

        Order by endpoint

    .. describe:: --methods, -m

        Order by methods

.. describe:: flaskbb makeconfig

    Generates a FlaskBB configuration file.

    .. describe:: --development, -d

        Creates a development config with DEBUG set to True.

    .. describe:: --output, -o

        The path where the config file will be saved at.
        Defaults to the flaskbb's root folder.

    .. describe:: --force, -f

        Overwrites any existing config file, if one exsits, WITHOUT asking.

.. describe:: flaskbb reindex

    Reindexes the search index.

.. describe:: flaskbb translations

    Translations command sub group.

    .. describe:: new LANGUAGE_CODE

        Adds a new language to FlaskBB's translations.
        The ``LANGUAGE_CODE`` is the short identifier for the language i.e.
        '``en``', '``de``', '``de_AT``', etc.

        .. describe:: --plugin PLUGIN_NAME, --p PLUGIN_NAME

            Adds a new language to a plugin.

    .. describe:: update

        Updates the translations.

        .. describe:: --all, -a

            Updates all translations, including the ones from the plugins.

        .. describe:: --plugin PLUGIN_NAME, --p PLUGIN_NAME

            Update the language of the given plugin.

    .. describe:: compile

        Compiles the translations.

        .. describe:: --all, -a

            Compiles all translations, including the ones from the plugins.

        .. describe:: --plugin PLUGIN_NAME, --p PLUGIN_NAME

            Compiles only the given plugin translation.

.. describe:: flaskbb plugins

    Plugins command sub group.

    .. describe:: new PLUGIN_IDENTIFIER

        Creates a new plugin based on the cookiecutter plugin template.
        Defaults to this template:
        https://github.com/sh4nks/cookiecutter-flaskbb-plugin.
        It will either accept a valid path on the filesystem
        or a URL to a Git repository which contains the cookiecutter template.

    .. describe:: install PLUGIN_IDENTIFIER

        Installs a plugin by using the plugin's identifier.

    .. describe:: uninstall PLUGIN_IDENTIFIER

        Uninstalls a plugin by using the plugin's identifier.

    .. describe:: remove PLUGIN_IDENTIFIER

        Removes a plugin from the filesystem by using the plugin's identifier.

        describe:: --force, -f

            Removes the plugin without asking for confirmation first.

    .. describe:: list

        Lists all installed plugins.

.. describe:: flaskbb themes

    Themes command sub group.

    .. describe:: new THEME_IDENTIFIER

        Creates a new theme based on the cookiecutter theme
        template. Defaults to this template:
        https://github.com/sh4nks/cookiecutter-flaskbb-theme.
        It will either accept a valid path on the filesystem
        or a URL to a Git repository which contains the cookiecutter template.

    .. describe:: remove THEME_IDENTIFIER

        Removes a theme from the filesystem by the theme's identifier.

    .. describe:: list

        Lists all installed themes.

.. describe:: flaskbb users

    Creates a new user. If an option is missing, you will be interactivly
    prompted to type it.

    .. describe:: new

        Creates a new user.

        .. describe:: --username USERNAME, -u USERNAME

            The username of the user.

        .. describe:: --email EMAIL, -e EMAIL

            The email address of the user.

        .. describe:: --password PASSWORD, -p PASSWORD

            The password of the user.

        .. describe:: --group GROUP, -g GROUP

            The primary group of the user. The group ``GROUP`` has to be
            one of ``admin``, ``super_mod``, ``mod`` or ``member``.

    .. describe:: update

        Updates an user.

        .. describe:: --username USERNAME, -u USERNAME

            The username of the user.

        .. describe:: --email EMAIL, -e EMAIL

            The email address of the user.

        .. describe:: --password PASSWORD, -p PASSWORD

            The password of the user.

        .. describe:: --group GROUP, -g GROUP

            The primary group of the user. The group ``GROUP`` has to be
            one of ``admin``, ``super_mod``, ``mod`` or ``member``.

    .. describe:: delete

        .. describe:: --username USERNAME, -u USERNAME

            The username of the user.

        .. describe:: --force, -f

            Removes the user without asking for confirmation first.
