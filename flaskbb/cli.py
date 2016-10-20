# -*- coding: utf-8 -*-
"""
    flaskbb.cli
    ~~~~~~~~~~~

    FlaskBB's Command Line Interface.
    To make it work, you have to install FlaskBB via ``pip install -e .``.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
import re
import time

import click
from flask.cli import FlaskGroup, with_appcontext
from sqlalchemy.exc import IntegrityError
from sqlalchemy_utils.functions import database_exists, drop_database
from flask_migrate import upgrade as upgrade_database

from flaskbb import create_app
from flaskbb._compat import iteritems
from flaskbb.extensions import db, whooshee, plugin_manager
from flaskbb.utils.populate import (create_test_data, create_welcome_forum,
                                    create_user, create_default_groups,
                                    create_default_settings, insert_bulk_data,
                                    update_settings_from_fixture)
from flaskbb.utils.translations import (add_translations, compile_translations,
                                        update_translations,
                                        add_plugin_translations,
                                        compile_plugin_translations,
                                        update_plugin_translations)

_email_regex = r"[^@]+@[^@]+\.[^@]+"


class FlaskBBCLIError(click.ClickException):
    """An exception that signals a usage error including color support.
    This aborts any further handling.

    :param styles: The style kwargs which should be forwarded to click.secho.
    """
    def __init__(self, message, **styles):
        click.ClickException.__init__(self, message)
        self.styles = styles

    def show(self, file=None):
        if file is None:
            file = click._compat.get_text_stderr()
        click.secho("[-] Error: %s" % self.format_message(), file=file,
                    **self.styles)


class EmailType(click.ParamType):
    """The choice type allows a value to be checked against a fixed set of
    supported values.  All of these values have to be strings.
    See :ref:`choice-opts` for an example.
    """
    name = "email"

    def convert(self, value, param, ctx):
        # Exact match
        if re.match(_email_regex, value):
            return value
        else:
            self.fail(("invalid email: %s" % value), param, ctx)

    def __repr__(self):
        return "email"


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """This is the commandline interface for flaskbb."""
    pass


@cli.command()
@click.option("--welcome-forum", default=True, is_flag=True,
              help="Creates a welcome forum.")
def install(welcome_forum):
    """Installs flaskbb. If no arguments are used, an interactive setup
    will be run.
    """
    click.secho("[+] Installing FlaskBB...", fg="cyan")
    if database_exists(db.engine.url):
        if click.confirm(click.style(
            "Existing database found. Do you want to delete the old one and "
            "create a new one?", fg="magenta")
        ):
            drop_database(db.engine.url)
            upgrade_database()
        else:
            sys.exit(0)
    else:
        upgrade_database()

    click.secho("[+] Creating default settings...", fg="cyan")
    create_default_groups()
    create_default_settings()

    click.secho("[+] Creating admin user...", fg="cyan")
    username = click.prompt(
        click.style("Username", fg="magenta"), type=str,
        default=os.environ.get("USER", "")
    )
    email = click.prompt(
        click.style("Email address", fg="magenta"), type=EmailType()
    )
    password = click.prompt(
        click.style("Password", fg="magenta"), hide_input=True,
        confirmation_prompt=True
    )
    group = click.prompt(
        click.style("Group", fg="magenta"),
        type=click.Choice(["admin", "super_mod", "mod", "member"]),
        default="admin"
    )
    create_user(username, password, email, group)

    if welcome_forum:
        click.secho("[+] Creating welcome forum...", fg="cyan")
        create_welcome_forum()

    click.secho("[+] Compiling translations...", fg="cyan")
    compile_translations()

    click.secho("[+] FlaskBB has been successfully installed!",
                fg="green", bold=True)


@cli.command()
@click.option("--test-data", "-t", default=False, is_flag=True,
              help="Adds some test data.")
@click.option("--bulk-data", "-b", default=False, is_flag=True,
              help="Adds a lot of data.")
@click.option("--posts", default=100,
              help="Number of posts to create in each topic (default: 100).")
@click.option("--topics", default=100,
              help="Number of topics to create (default: 100).")
@click.option("--force", "-f", is_flag=True,
              help="Will delete the database before populating it.")
@click.option("--initdb", "-i", is_flag=True,
              help="Initializes the database before populating it.")
def populate(bulk_data, test_data, posts, topics, force, initdb):
    """Creates the necessary tables and groups for FlaskBB."""
    if force:
        click.secho("[+] Recreating database...", fg="cyan")
        drop_database(db.engine.url)
        upgrade_database()

    if initdb:
        upgrade_database()

    if test_data:
        click.secho("[+] Adding some test data...", fg="cyan")
        create_test_data()

    if bulk_data:
        timer = time.time()
        topic_count, post_count = insert_bulk_data(int(topics), int(posts))
        elapsed = time.time() - timer
        click.secho("[+] It took {} seconds to create {} topics and {} posts"
                    .format(elapsed, topic_count, post_count), fg="cyan")


@cli.group()
def translations():
    """Translations command sub group."""
    pass


@translations.command("new")
@click.option("--plugin", "-p", type=click.STRING,
              help="The plugin for which a language should be added.")
@click.argument("lang")
def new_translation(lang, plugin):
    """Adds a new language to the translations. "lang" is the language code
    of the language, like, "de_AT"."""
    if plugin:
        if plugin not in plugin_manager.all_plugins:
            raise FlaskBBCLIError("Plugin {} not found.".format(plugin),
                                  fg="red")
        click.secho("[+] Adding new language {} for plugin {}..."
                    .format(lang, plugin), fg="cyan")
        add_plugin_translations(plugin, lang)
    else:
        click.secho("[+] Adding new language {}...".format(lang), fg="cyan")
        add_translations(lang)


@translations.command("update")
@click.option("is_all", "--all", "-a", default=True, is_flag=True,
              help="Updates the plugin translations as well.")
@click.option("--plugin", "-p", type=click.STRING,
              help="The plugin for which the translations should be updated.")
def update_translation(is_all, plugin):
    """Updates all translations."""
    if plugin is not None:
        if plugin not in plugin_manager.all_plugins:
            raise FlaskBBCLIError("Plugin {} not found.".format(plugin),
                                  fg="red")

        click.secho("[+] Updating language files for plugin {}..."
                    .format(plugin), fg="cyan")
        update_plugin_translations(plugin)
    else:
        click.secho("[+] Updating language files...", fg="cyan")
        update_translations(include_plugins=is_all)


@translations.command("compile")
@click.option("is_all", "--all", "-a", default=True, is_flag=True,
              help="Compiles the plugin translations as well.")
@click.option("--plugin", "-p", type=click.STRING,
              help="The plugin for which the translations should be compiled.")
def compile_translation(is_all, plugin):
    """Compiles all translations."""
    if plugin is not None:
        if plugin not in plugin_manager.all_plugins:
            raise FlaskBBCLIError("Plugin {} not found.".format(plugin),
                                  fg="red")
        click.secho("[+] Compiling language files for plugin {}..."
                    .format(plugin), fg="cyan")
        compile_plugin_translations(plugin)
    else:
        click.secho("[+] Compiling language files...", fg="cyan")
        compile_translations(include_plugins=is_all)


@cli.group()
def plugins():
    """Plugins command sub group."""
    pass


@plugins.command("new")
@click.argument("plugin")
def new_plugin(plugin):
    """Creates a new plugin based on the plugin template."""
    click.secho("[+] Creating new Plugin {}...".format(plugin), fg="cyan")


@plugins.command("install")
@click.argument("plugin")
def install_plugin(plugin):
    """Installs a new plugin from FlaskBB"s Plugin Repository."""
    click.secho("[+] Installing plugin {}...".format(plugin), fg="cyan")


@plugins.command("uninstall")
@click.argument("plugin")
def uninstall_plugin(plugin):
    """Uninstalls a plugin from FlaskBB."""
    click.secho("[+] Uninstalling plugin {}...".format(plugin), fg="cyan")


@plugins.command("list")
def list_plugins():
    """Lists all installed plugins."""
    pass


@cli.group()
def themes():
    """Themes command sub group."""
    pass


@cli.group()
def users():
    """Create, update or delete users."""
    pass


@users.command("new")
@click.option("--username", prompt=True,
              default=lambda: os.environ.get("USER", ""),
              help="The username of the new user.")
@click.option("--email", prompt=True, type=EmailType(),
              help="The email address of the new user.")
@click.option("--password", prompt=True, hide_input=True,
              confirmation_prompt=True,
              help="The password of the new user.")
@click.option("--group", prompt=True, default="member",
              type=click.Choice(["admin", "super_mod", "mod", "member"]))
def new_user(username, email, password, group):
    """Creates a new user. Omit any options to use the interactive mode."""
    try:
        user = create_user(username, password, email, group)

        click.secho("[+] User {} with Email {} in Group {} created.".format(
            user.username, user.email, user.primary_group.name), fg="cyan"
        )
    except IntegrityError:
        raise FlaskBBCLIError("Couldn't create the user because the "
                              "username or email address is already taken.",
                              fg="red")


@cli.command()
def reindex():
    """Reindexes the search index."""
    click.secho("Reindexing search index...", fg="cyan")
    whooshee.reindex()


@cli.command()
@click.option("--all", "-a", default=True, is_flag=True,
              help="Upgrades migrations AND fixtures to the latest version.")
@click.option("--fixture/", "-f", default=None,
              help="The fixture which should be upgraded or installed.")
@click.option("--force-fixture", "-ff", default=False, is_flag=True,
              help="Forcefully upgrades the fixtures.")
def upgrade(all, fixture, force_fixture):
    """Updates the migrations and fixtures."""
    update_settings_from_fixture(fixture, overwrite_setting=force_fixture)


@cli.command()
@click.option("--server", "-s", default="gunicorn",
              type=click.Choice(["gunicorn", "gevent"]),
              help="The WSGI Server to run FlaskBB on.")
@click.option("--host", "-h", default="127.0.0.1",
              help="The interface to bind FlaskBB to.")
@click.option("--port", "-p", default="8000", type=int,
              help="The port to bind FlaskBB to.")
@click.option("--workers", "-w", default=4,
              help="The number of worker processes for handling requests.")
@click.option("--daemon", "-d", default=False, is_flag=True,
              help="Starts gunicorn as daemon.")
@click.option("--config", "-c",
              help="The configuration file to use for FlaskBB.")
def start(server, host, port, workers, config, daemon):
    """Starts a production ready wsgi server.
    TODO: Figure out a way how to forward additional args to gunicorn
          without causing any errors.
    """
    if server == "gunicorn":
        try:
            from gunicorn.app.base import Application

            class FlaskBBApplication(Application):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super(FlaskBBApplication, self).__init__()

                def load_config(self):
                    config = dict([
                        (key, value) for key, value in iteritems(self.options)
                        if key in self.cfg.settings and value is not None
                    ])
                    for key, value in iteritems(config):
                        self.cfg.set(key.lower(), value)

                def load(self):
                    return self.application

            options = {
                "bind": "{}:{}".format(host, port),
                "workers": workers,
                "daemon": daemon,
            }
            FlaskBBApplication(create_app(config=config), options).run()
        except ImportError:
            raise FlaskBBCLIError("Cannot import gunicorn. "
                                  "Make sure it is installed.", fg="red")

    elif server == "gevent":
        try:
            from gevent import __version__
            from gevent.pywsgi import WSGIServer
            click.secho("* Starting gevent {}".format(__version__))
            click.secho("* Listening on http://{}:{}/".format(host, port))
            http_server = WSGIServer((host, port), create_app(config=config))
            http_server.serve_forever()
        except ImportError:
            raise FlaskBBCLIError("Cannot import gevent. "
                                  "Make sure it is installed.", fg="red")


@cli.command("shell", short_help="Runs a shell in the app context.")
@with_appcontext
def shell_command():
    """Runs an interactive Python shell in the context of a given
    Flask application.  The application will populate the default
    namespace of this shell according to it"s configuration.
    This is useful for executing small snippets of management code
    without having to manually configuring the application.

    This code snippet is taken from Flask"s cli module and modified to
    run IPython and falls back to the normal shell if IPython is not
    available.
    """
    import code
    from flask import _app_ctx_stack
    app = _app_ctx_stack.top.app
    banner = "Python %s on %s\nInstance Path: %s" % (
        sys.version,
        sys.platform,
        app.instance_path,
    )
    ctx = {"db": db}

    # Support the regular Python interpreter startup script if someone
    # is using it.
    startup = os.environ.get("PYTHONSTARTUP")
    if startup and os.path.isfile(startup):
        with open(startup, "r") as f:
            eval(compile(f.read(), startup, "exec"), ctx)

    ctx.update(app.make_shell_context())

    try:
        import IPython
        IPython.embed(banner1=banner, user_ns=ctx)
    except ImportError:
        code.interact(banner=banner, local=ctx)


@cli.command("urls")
@click.option("--order", default="rule", help="Property on Rule to order by.")
def list_urls(order):
    """Lists all available routes.
    Taken from Flask-Script: https://goo.gl/K6NCAz"""
    from flask import current_app

    rows = []
    column_length = 0
    column_headers = ("Rule", "Endpoint", "Arguments")

    rules = sorted(
        current_app.url_map.iter_rules(),
        key=lambda rule: getattr(rule, order)
    )
    for rule in rules:
        rows.append((rule.rule, rule.endpoint, None))
    column_length = 2

    str_template = ""
    table_width = 0

    if column_length >= 1:
        max_rule_length = max(len(r[0]) for r in rows)
        max_rule_length = max_rule_length if max_rule_length > 4 else 4
        str_template += "%-" + str(max_rule_length) + "s"
        table_width += max_rule_length

    if column_length >= 2:
        max_endpoint_len = max(len(str(r[1])) for r in rows)
        # max_endpoint_len = max(rows, key=len)
        max_endpoint_len = max_endpoint_len if max_endpoint_len > 8 else 8
        str_template += "  %-" + str(max_endpoint_len) + "s"
        table_width += 2 + max_endpoint_len

    if column_length >= 3:
        max_args_len = max(len(str(r[2])) for r in rows)
        max_args_len = max_args_len if max_args_len > 9 else 9
        str_template += "  %-" + str(max_args_len) + "s"
        table_width += 2 + max_args_len

    print(str_template % (column_headers[:column_length]))
    print("-" * table_width)

    for row in rows:
        print(str_template % row[:column_length])
