.. _commandline:

Command Line Interface
======================

Here you can find the documentation about FlaskBB's Command Line Interface.

To get help for a commands, just type ``flaskbb COMMAND --help``.
If no command options or arguments are used it will display all available
commands.

.. sourcecode:: text

    Usage: flaskbb [OPTIONS] [COMMAND] [ARGS]...

      This is the commandline interface for flaskbb.

    Options:
      --config CONFIG       Specify the config to use either in dotted module
                            notation e.g. 'flaskbb.configs.default.DefaultConfig'
                            or by using a path like '/path/to/flaskbb.cfg'
      --instance PATH       Specify the instance path to use. By default the
                            folder 'instance' next to the package or module is
                            assumed to be the instance path.
      --version             Show the FlaskBB version.
      -e, --env-file FILE   Load environment variables from this file, taking
                            precedence over those set by '.env' and '.flaskenv'.
                            Variables set directly in the environment take
                            highest precedence. python-dotenv must be installed.
      --debug / --no-debug  Set debug mode.
      --help                Show this message and exit.

    Commands:
      celery        Preconfigured wrapper around the 'celery' command.
      db            Perform database migrations (Flask-Alembic).
      groups        Create, update or delete groups.
      install       Installs flaskbb.
      makeconfig    Generates a FlaskBB configuration file.
      permissions   Show or modify the permissions of the groups.
      plugins       Plugins command sub group.
      populate      Creates the necessary tables and groups for FlaskBB.
      reindex       Reindexes the search index.
      routes        Show the routes for the app (Flask's built-in command).
      run           Runs a development server.
      shell         Runs a shell in the app context.
      themes        Themes command sub group.
      translations  Translations command sub group.
      urls          Show routes for the app.
      users         Create, update or delete users.

``-e/--env-file`` and ``--debug/--no-debug`` are provided by
Flask's own :class:`~flask.cli.FlaskGroup` - see the `Flask CLI documentation
<https://flask.palletsprojects.com/en/latest/cli/>`_ for details on those.


Commands
--------

Here you will find a detailed description of every command including all
of their options and arguments.

``flaskbb install``
~~~~~~~~~~~~~~~~~~~

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

.. describe:: --no-plugins, -n

    Don't run the migrations for the default plugins.

``flaskbb populate``
~~~~~~~~~~~~~~~~~~~~

Creates the necessary tables and groups for FlaskBB.

.. describe:: --test-data, -t

    Adds some test data.

.. describe:: --bulk-data, -b

    Adds a lot of test data. Combine with ``--posts`` and ``--topics``
    to control how much is generated.

.. describe:: --posts

    Number of posts to create in each topic (default: 100).

.. describe:: --topics

    Number of topics to create (default: 100).

.. describe:: --force, -f

    Will delete the database without asking before populating it.

.. describe:: --initdb, -i

    Initializes the database before populating it.

``flaskbb run``
~~~~~~~~~~~~~~~

Runs a local development server (Flask's built-in ``run`` command). This
server is for development purposes only - it does not provide the
stability, security, or performance of a production WSGI server. See
:ref:`production-deployment` for how to deploy FlaskBB with gunicorn/uWSGI in
production.

.. describe:: --debug, --no-debug

    Set debug mode. Enables the reloader and debugger by default.

.. describe:: --host HOST, -h HOST

    The interface to bind to.

.. describe:: --port PORT, -p PORT

    The port to bind to.

.. describe:: --cert PATH

    Specify a certificate file to use HTTPS.

.. describe:: --key FILE

    The key file to use when specifying a certificate.

.. describe:: --reload, --no-reload

    Enable or disable the reloader. Active by default if debug is
    enabled.

.. describe:: --debugger, --no-debugger

    Enable or disable the debugger. Active by default if debug is
    enabled.

.. describe:: --with-threads, --without-threads

    Enable or disable multithreading.

.. describe:: --extra-files PATH

    Extra files that trigger a reload on change. Multiple paths are
    separated by ``:``.

.. describe:: --exclude-patterns PATH

    Files matching these fnmatch patterns will not trigger a reload on
    change. Multiple patterns are separated by ``:``.

``flaskbb serve``
~~~~~~~~~~~~~~~~~

Serves FlaskBB with gunicorn. This requires the ``gunicorn`` extra to be
installed (``uv sync --extra gunicorn``). Options that are not listed below
can be set through a gunicorn configuration file.

.. describe:: --host HOST, -h HOST

    The interface to bind FlaskBB to. Defaults to ``127.0.0.1``.

.. describe:: --port PORT, -p PORT

    The port to bind FlaskBB to. Defaults to ``8000``.

.. describe:: --workers WORKERS, -w WORKERS

    The number of worker processes for handling requests. Defaults to ``1``.

.. describe:: --worker-class CLASS, -k CLASS

    The type of worker to use. Defaults to ``sync``.

.. describe:: --daemon, -d

    Runs gunicorn in the background.

.. describe:: --gunicorn-config FILE, -c FILE

    A gunicorn configuration file. Options given on the command line take
    precedence over the ones in the configuration file.

``flaskbb celery CELERY_ARGS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Starts celery. This is just a preconfigured wrapper around the ``celery``
command. Additional arguments are directly passed to celery, e.g.
``flaskbb celery worker`` or ``flaskbb celery beat``.

``flaskbb shell``
~~~~~~~~~~~~~~~~~

Creates a python shell with an app context.

``flaskbb urls``
~~~~~~~~~~~~~~~~

Lists all available routes.

.. describe:: --route, -r

    Order by route.

.. describe:: --endpoint, -e

    Order by endpoint

.. describe:: --methods, -m

    Order by methods

``flaskbb routes``
~~~~~~~~~~~~~~~~~~

Flask's own built-in command for showing all registered routes with
their endpoints and methods. Similar to ``flaskbb urls`` above, but comes
from Flask itself rather than FlaskBB.

.. describe:: --sort [endpoint|methods|domain|rule|match], -s [endpoint|methods|domain|rule|match]

    Method to sort routes by. ``match`` is the order in which Flask
    will match routes when dispatching a request.

.. describe:: --all-methods

    Show HEAD and OPTIONS methods too.

``flaskbb makeconfig``
~~~~~~~~~~~~~~~~~~~~~~

Generates a FlaskBB configuration file.

.. describe:: --development, -d

    Creates a development config with DEBUG set to True.

.. describe:: --output, -o

    The path where the config file will be saved at.
    Defaults to the flaskbb's root folder.

.. describe:: --force, -f

    Overwrites any existing config file, if one exsits, WITHOUT asking.

``flaskbb reindex``
~~~~~~~~~~~~~~~~~~~

Reindexes the search index.

``flaskbb db``
~~~~~~~~~~~~~~

Runs database migrations. This sub group is provided by
`Flask-Alembic <https://flask-alembic.readthedocs.io/>`_ and mirrors its
CLI 1:1 - see its documentation for the full details of each command.
FlaskBB uses alembic's branching feature so each plugin gets its own
migration branch, keyed by the plugin's name.

.. describe:: revision MESSAGE

    Generate a new revision.

    .. describe:: --branch NAME, -b NAME

        Use this independent branch name, e.g. the plugin's name, so
        ``flaskbb db revision --branch portal "add forum_ids column"``.

    .. describe:: --parent REVISION, -p REVISION

        Parent revision(s) of this revision.

    .. describe:: --empty

        Create an empty script.

    .. describe:: --splice

        Allow non-head parent revision.

    .. describe:: --depend REVISION, -d REVISION

        Revision(s) this revision depends on.

    .. describe:: --label LABEL, -l LABEL

        Label(s) to apply to the revision.

    .. describe:: --path PATH

        Where to store the revision.

.. describe:: upgrade [TARGET]

    Run migrations to upgrade the database. ``TARGET`` defaults to
    ``heads``, which upgrades FlaskBB and every enabled plugin, and can
    be scoped to a single branch, e.g. ``flaskbb db upgrade portal@head``.

.. describe:: downgrade [TARGET]

    Run migrations to downgrade the database, e.g.
    ``flaskbb db downgrade portal@base`` to undo all of a plugin's
    migrations.

.. describe:: stamp [TARGET]

    Set the current revision without running migrations.

.. describe:: current

    Show the list of current revisions.

    .. describe:: --check-heads

        Check if all head revisions are applied.

.. describe:: heads

    Show the list of revisions that have no child revisions.

    .. describe:: --resolve-dependencies

        Treat dependencies as down revisions.

.. describe:: branches

    Show the list of revisions that have more than one next revision.

.. describe:: log

    Show the list of revisions in the order they will run.

    .. describe:: --start REVISION

        Show since this revision.

    .. describe:: --end REVISION

        Show until this revision.

.. describe:: show [REVISIONS]

    Show the given revisions.

.. describe:: merge [REVISIONS]

    Generate a merge revision.

    .. describe:: --message MESSAGE, -m MESSAGE

        The message for the merge revision.

    .. describe:: --label LABEL, -l LABEL

        Label(s) to apply to the revision.

.. describe:: check

    Check if any changes between the database and models are detected.

.. describe:: mkdir

    Create the migration directory if it does not exist.

``flaskbb translations``
~~~~~~~~~~~~~~~~~~~~~~~~

Translations command sub group.

.. describe:: new LANG

    Adds a new language to FlaskBB's translations.
    ``LANG`` is the short identifier for the language i.e.
    '``en``', '``de``', '``de_AT``', etc.

    .. describe:: --plugin PLUGIN_NAME, -p PLUGIN_NAME

        Adds a new language to a plugin instead of to core.

.. describe:: update

    Updates the translations.

    .. describe:: --all, -a

        Updates all translations, including the ones from the plugins.

    .. describe:: --plugin PLUGIN_NAME, -p PLUGIN_NAME

        Update the language of the given plugin.

.. describe:: compile

    Compiles the translations.

    .. describe:: --all, -a

        Compiles all translations, including the ones from the plugins.

    .. describe:: --plugin PLUGIN_NAME, -p PLUGIN_NAME

        Compiles only the given plugin translation.

``flaskbb plugins``
~~~~~~~~~~~~~~~~~~~

Plugins command sub group. See :ref:`plugins` for the full
install/uninstall/enable/disable workflow.

.. describe:: new PLUGIN_IDENTIFIER

    Creates a new plugin based on the cookiecutter plugin template.
    Defaults to this template:
    https://github.com/sh4nks/cookiecutter-flaskbb-plugin.
    It will either accept a valid path on the filesystem
    or a URL to a Git repository which contains the cookiecutter template.

    .. describe:: --template TEMPLATE, -t TEMPLATE

        Path to a cookiecutter template or to a valid git repo.

    .. describe:: --out-dir PATH, -o PATH

        The location for the new FlaskBB plugin.

    .. describe:: --force, -f

        Overwrite the contents of the output directory if it exists.

.. describe:: install [PLUGIN_NAME]

    Installs a plugin's settings and applies its migrations (if the
    plugin has any).

    .. describe:: --all, -a

        Installs all plugins instead of a single one. Either this or
        ``PLUGIN_NAME`` has to be given.

    .. describe:: --settings-only, -s

        Only installs the settings.

    .. describe:: --migrations-only, -m

        Only applies the migrations. Mutually exclusive with
        ``--settings-only``.

    .. describe:: --force, -f

        Overwrites existing settings.

.. describe:: uninstall [PLUGIN_NAME]

    Uninstalls a plugin's settings and reverts its migrations (if the
    plugin has any). Reverting the migrations drops the plugin's tables,
    so this asks for confirmation first.

    .. describe:: --all, -a

        Uninstalls all plugins instead of a single one. Either this or
        ``PLUGIN_NAME`` has to be given.

    .. describe:: --settings-only, -s

        Only removes the settings. No confirmation is asked for since
        nothing is dropped.

    .. describe:: --migrations-only, -m

        Only reverts the migrations. Mutually exclusive with
        ``--settings-only``.

    .. describe:: --force, -f

        Doesn't ask for confirmation.

.. describe:: upgrade [PLUGIN_NAME]

    Upgrades a plugin's settings to match its currently registered
    :class:`~flaskbb.core.settings.definitions.SettingGroup` and applies
    its newest migrations - use this after upgrading a plugin whose
    settings or database schema changed between versions.

    .. describe:: --all, -a

        Upgrades all plugins instead of a single one. Either this or
        ``PLUGIN_NAME`` has to be given.

    .. describe:: --settings-only, -s

        Only upgrades the settings.

    .. describe:: --migrations-only, -m

        Only applies the migrations. Mutually exclusive with
        ``--settings-only``.

.. describe:: enable PLUGIN_NAME

    Enables a plugin.

.. describe:: disable PLUGIN_NAME

    Disables a plugin.

.. describe:: list

    Lists all installed plugins.

.. describe:: cleanup

    Removes zombie plugins from FlaskBB - a zombie plugin is one that
    has a row in the database but is no longer installed in the
    environment.

``flaskbb themes``
~~~~~~~~~~~~~~~~~~

Themes command sub group.

.. describe:: new THEME_IDENTIFIER

    Creates a new theme based on the cookiecutter theme
    template. Defaults to this template:
    https://github.com/sh4nks/cookiecutter-flaskbb-theme.
    It will either accept a valid path on the filesystem
    or a URL to a Git repository which contains the cookiecutter template.

    .. describe:: --template TEMPLATE, -t TEMPLATE

        Path to a cookiecutter template or to a valid git repo.

    .. describe:: --out-dir PATH, -o PATH

        The location for the new FlaskBB theme.

    .. describe:: --force, -f

        Overwrite the contents of the output directory if it exists.

.. describe:: remove THEME_IDENTIFIER

    Removes a theme from the filesystem by the theme's identifier.

    .. describe:: --force, -f

        Removes the theme without asking for confirmation first.

.. describe:: list

    Lists all installed themes.

``flaskbb users``
~~~~~~~~~~~~~~~~~

Create, update or delete users. Omit an option to be prompted for it
interactively.

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

    Deletes a user.

    .. describe:: --username USERNAME, -u USERNAME

        The username of the user.

    .. describe:: --force, -f

        Removes the user without asking for confirmation first.

.. describe:: list

    Lists all users.

    .. describe:: --group GROUP, -g GROUP

        Only show users who have ``GROUP`` as their primary or as one of
        their secondary groups.

    .. describe:: --banned, -b

        Only show banned users.

    .. describe:: --unactivated, -U

        Only show users who haven't activated their account yet.

.. describe:: show USERNAME

    Shows a user including his groups and the permissions they grant him.

.. describe:: ban USERNAME

    Bans a user by moving him into the banned group.

.. describe:: unban USERNAME

    Unbans a user by moving him back into the member group. Note that this
    doesn't restore the group the user was in before he got banned.

.. describe:: activate USERNAME

    Activates a user's account.

.. describe:: deactivate USERNAME

    Deactivates a user's account.

.. describe:: set-group USERNAME GROUP

    Sets the primary group of a user. If ``GROUP`` is one of the user's
    secondary groups it is removed from those - a group is either the
    primary or a secondary group, never both.

.. describe:: add-group USERNAME GROUP

    Adds a user to a secondary group.

.. describe:: remove-group USERNAME GROUP

    Removes a user from a secondary group.

``flaskbb groups``
~~~~~~~~~~~~~~~~~~

Create, update or delete groups. The name of a group is case insensitive.

.. describe:: list

    Lists all groups including their type and how many members they have.

.. describe:: show NAME

    Shows a group including its permissions.

.. describe:: new NAME

    Creates a new group. Permissions that are neither granted nor revoked
    are set to their default value, e.g.::

        flaskbb groups new VIP --description "Trusted members" \
            --grant viewhidden --revoke postattachment

    .. describe:: --description TEXT, -d TEXT

        The description of the group.

    .. describe:: --type TYPE, -t TYPE

        The type of the group, one of ``admin``, ``super_mod``, ``mod``,
        ``banned`` or ``guest``. Omit it to create an ordinary member
        group. There can only be one ``guest`` and one ``banned`` group.

    .. describe:: --grant PERMISSION

        A permission to grant. Can be used multiple times.

    .. describe:: --revoke PERMISSION

        A permission to revoke. Can be used multiple times.

.. describe:: update NAME

    Updates a group. Any option that is omitted is left unchanged. It takes
    the same options as ``new`` plus:

    .. describe:: --name NAME, -n NAME

        The new name of the group.

    ``--type`` additionally accepts ``member`` here, which turns a typed
    group back into an ordinary one.

.. describe:: delete NAME

    Deletes a group. The six groups that are created during the
    installation can't be deleted, neither can groups that still have
    members.

    .. describe:: --force, -f

        Removes the group without asking for confirmation first.

``flaskbb permissions``
~~~~~~~~~~~~~~~~~~~~~~~

Show or modify the permissions of the groups.

.. describe:: list

    Lists the permissions of every group as a table.

    .. describe:: --group GROUP, -g GROUP

        Only show the permissions of this group.

.. describe:: show USERNAME

    Shows the effective permissions of a user and which of his groups grant
    them.

.. describe:: set GROUP PERMISSION VALUE

    Grants or revokes a single permission of a group, where ``VALUE`` is a
    boolean, e.g.::

        flaskbb permissions set Member deletepost true
