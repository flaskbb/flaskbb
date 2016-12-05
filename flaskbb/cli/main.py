# -*- coding: utf-8 -*-
"""
    flaskbb.cli.commands
    ~~~~~~~~~~~~~~~~~~~~

    This module contains the main commands.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
import time
import requests

import click
from werkzeug.utils import import_string, ImportStringError
from flask import current_app
from flask.cli import FlaskGroup, ScriptInfo, with_appcontext
from sqlalchemy_utils.functions import database_exists, drop_database
from flask_migrate import upgrade as upgrade_database

from flaskbb import create_app
from flaskbb._compat import iteritems
from flaskbb.extensions import db, whooshee, celery
from flaskbb.cli.utils import (get_version, save_user_prompt, FlaskBBCLIError,
                               EmailType)
from flaskbb.utils.populate import (create_test_data, create_welcome_forum,
                                    create_default_groups,
                                    create_default_settings, insert_bulk_data,
                                    update_settings_from_fixture)
from flaskbb.utils.translations import compile_translations


def make_app(script_info):
    config_file = getattr(script_info, "config_file")
    if config_file is not None:
        # check if config file exists
        if os.path.exists(os.path.abspath(config_file)):
            click.secho("[+] Using config from: {}".format(
                        os.path.abspath(config_file)), fg="cyan")
        # config file doesn't exist, maybe it's a module
        else:
            try:
                import_string(config_file)
                click.secho("[+] Using config from: {}".format(config_file),
                            fg="cyan")
            except ImportStringError:
                click.secho("[~] Config '{}' doesn't exist. "
                            "Using default config.".format(config_file),
                            fg="red")
                config_file = None
    else:
        click.secho("[~] Using default config.", fg="yellow")

    return create_app(config_file)


def set_config(ctx, param, value):
    """This will pass the config file to the create_app function."""
    ctx.ensure_object(ScriptInfo).config_file = value


@click.group(cls=FlaskGroup, create_app=make_app)
@click.option("--version", expose_value=False, callback=get_version,
              is_flag=True, is_eager=True, help="Show the FlaskBB version.")
@click.option("--config", expose_value=False, callback=set_config,
              required=False, is_flag=False, is_eager=True,
              help="Specify the config to use in dotted module notation "
                   "e.g. flaskbb.configs.default.DefaultConfig")
def flaskbb():
    """This is the commandline interface for flaskbb."""
    pass


@flaskbb.command()
@click.option("--welcome", "-w", default=True, is_flag=True,
              help="Disable the welcome forum.")
@click.option("--force", "-f", default=False, is_flag=True,
              help="Doesn't ask for confirmation.")
@click.option("--username", "-u", help="The username of the user.")
@click.option("--email", "-e", type=EmailType(),
              help="The email address of the user.")
@click.option("--password", "-p", help="The password of the user.")
@click.option("--group", "-g", help="The group of the user.",
              type=click.Choice(["admin", "super_mod", "mod", "member"]))
def install(welcome, force, username, email, password, group):
    """Installs flaskbb. If no arguments are used, an interactive setup
    will be run.
    """
    click.secho("[+] Installing FlaskBB...", fg="cyan")
    if database_exists(db.engine.url):
        if force or click.confirm(click.style(
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
    save_user_prompt(username, email, password, group)

    if welcome:
        click.secho("[+] Creating welcome forum...", fg="cyan")
        create_welcome_forum()

    click.secho("[+] Compiling translations...", fg="cyan")
    compile_translations()

    click.secho("[+] FlaskBB has been successfully installed!",
                fg="green", bold=True)


@flaskbb.command()
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

        # do not initialize the db if -i is passed
        if not initdb:
            upgrade_database()

    if initdb:
        click.secho("[+] Initializing database...", fg="cyan")
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

    # this just makes the most sense for the command name; use -i to
    # init the db as well
    if not test_data:
        click.secho("[+] Populating the database with some defaults...",
                    fg="cyan")
        create_default_groups()
        create_default_settings()


@flaskbb.command()
def reindex():
    """Reindexes the search index."""
    click.secho("[+] Reindexing search index...", fg="cyan")
    whooshee.reindex()


@flaskbb.command()
@click.option("all_latest", "--all", "-a", default=False, is_flag=True,
              help="Upgrades migrations AND fixtures to the latest version.")
@click.option("--fixture/", "-f", default=None,
              help="The fixture which should be upgraded or installed.")
@click.option("--force", default=False, is_flag=True,
              help="Forcefully upgrades the fixtures.")
def upgrade(all_latest, fixture, force):
    """Updates the migrations and fixtures."""
    if all_latest:
        click.secho("[+] Upgrading migrations to the latest version...",
                    fg="cyan")
        upgrade_database()

    if fixture or all_latest:
        try:
            settings = import_string(
                "flaskbb.fixtures.{}".format(fixture)
            )
            settings = settings.fixture
        except ImportError:
            raise FlaskBBCLIError("{} fixture is not available"
                                  .format(fixture), fg="red")

        click.secho("[+] Updating fixtures...")
        count = update_settings_from_fixture(
            fixture=settings, overwrite_group=force, overwrite_setting=force
        )
        click.secho("[+] {} groups and {} settings updated.".format(
            len(count.keys()), len(count.values()), fg="green")
        )


@flaskbb.command("download-emojis")
@with_appcontext
def download_emoji():
    """Downloads emojis from emoji-cheat-sheet.com.
    This command is probably going to be removed in future version.
    """
    click.secho("[+] Downloading emojis...", fg="cyan")
    HOSTNAME = "https://api.github.com"
    REPO = "/repos/arvida/emoji-cheat-sheet.com/contents/public/graphics/emojis"
    FULL_URL = "{}{}".format(HOSTNAME, REPO)
    DOWNLOAD_PATH = os.path.join(current_app.static_folder, "emoji")
    response = requests.get(FULL_URL)

    cached_count = 0
    count = 0
    for image in response.json():
        if not os.path.exists(os.path.abspath(DOWNLOAD_PATH)):
            raise FlaskBBCLIError(
                "{} does not exist.".format(os.path.abspath(DOWNLOAD_PATH)),
                fg="red")

        full_path = os.path.join(DOWNLOAD_PATH, image["name"])
        if not os.path.exists(full_path):
            count += 1
            f = open(full_path, 'wb')
            f.write(requests.get(image["download_url"]).content)
            f.close()
            if count == cached_count + 50:
                cached_count = count
                click.secho("[+] {} out of {} Emojis downloaded...".format(
                            cached_count, len(response.json())), fg="cyan")

    click.secho("[+] Finished downloading {} Emojis.".format(count),
                fg="green")


@flaskbb.command("celery", context_settings=dict(ignore_unknown_options=True,))
@click.argument('celery_args', nargs=-1, type=click.UNPROCESSED)
@click.option("show_help", "--help", "-h", is_flag=True,
              help="Shows this message and exits")
@click.option("show_celery_help", "--help-celery", is_flag=True,
              help="Shows the celery help message")
@click.pass_context
@with_appcontext
def start_celery(ctx, show_help, show_celery_help, celery_args):
    """Preconfigured wrapper around the 'celery' command.
    Additional CELERY_ARGS arguments are passed to celery."""
    if show_help:
        click.echo(ctx.get_help())
        sys.exit(0)

    if show_celery_help:
        click.echo(celery.start(argv=["--help"]))
        sys.exit(0)

    default_args = ['celery']
    default_args = default_args + list(celery_args)
    celery.start(argv=default_args)


@flaskbb.command()
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


@flaskbb.command("shell", short_help="Runs a shell in the app context.")
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
    banner = "Python %s on %s\nInstance Path: %s" % (
        sys.version,
        sys.platform,
        current_app.instance_path,
    )
    ctx = {"db": db}

    # Support the regular Python interpreter startup script if someone
    # is using it.
    startup = os.environ.get("PYTHONSTARTUP")
    if startup and os.path.isfile(startup):
        with open(startup, "r") as f:
            eval(compile(f.read(), startup, "exec"), ctx)

    ctx.update(current_app.make_shell_context())

    try:
        import IPython
        IPython.embed(banner1=banner, user_ns=ctx)
    except ImportError:
        code.interact(banner=banner, local=ctx)


@flaskbb.command("urls", short_help="Show routes for the app.")
@click.option("--route", "-r", "order_by", flag_value="rule", default=True,
              help="Order by route")
@click.option("--endpoint", "-e", "order_by", flag_value="endpoint",
              help="Order by endpoint")
@click.option("--methods", "-m", "order_by", flag_value="methods",
              help="Order by methods")
@with_appcontext
def list_urls(order_by):
    """Lists all available routes."""
    from flask import current_app

    rules = sorted(
        current_app.url_map.iter_rules(),
        key=lambda rule: getattr(rule, order_by)
    )

    max_rule_len = max(len(rule.rule) for rule in rules)
    max_rule_len = max(max_rule_len, len("Route"))

    max_endpoint_len = max(len(rule.endpoint) for rule in rules)
    max_endpoint_len = max(max_endpoint_len, len("Endpoint"))

    max_method_len = max(len(", ".join(rule.methods)) for rule in rules)
    max_method_len = max(max_method_len, len("Methods"))

    column_header_len = max_rule_len + max_endpoint_len + max_method_len + 4
    column_template = "{:<%s}  {:<%s}  {:<%s}" % (
        max_rule_len, max_endpoint_len, max_method_len
    )

    click.secho(column_template.format("Route", "Endpoint", "Methods"),
                fg="blue", bold=True)
    click.secho("=" * column_header_len, bold=True)

    for rule in rules:
        methods = ", ".join(rule.methods)
        click.echo(column_template.format(rule.rule, rule.endpoint, methods))
