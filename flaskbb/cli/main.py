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
import binascii
from datetime import datetime

import click
from werkzeug.utils import import_string, ImportStringError
from jinja2 import Environment, FileSystemLoader
from flask import current_app
from flask.cli import FlaskGroup, ScriptInfo, with_appcontext
from sqlalchemy_utils.functions import database_exists, drop_database
from flask_alembic import alembic_click

from flaskbb import create_app
from flaskbb._compat import iteritems
from flaskbb.extensions import db, whooshee, celery, alembic
from flaskbb.cli.utils import (prompt_save_user, prompt_config_path,
                               write_config, get_version, FlaskBBCLIError,
                               EmailType)
from flaskbb.utils.populate import (create_test_data, create_welcome_forum,
                                    create_default_groups,
                                    create_default_settings, insert_bulk_data,
                                    update_settings_from_fixture,
                                    create_latest_db)
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
        # lets look for a config file in flaskbb's root folder
        # TODO: are there any other places we should look for the config?
        # Like somewhere in /etc/?

        # this walks back to flaskbb/ from flaskbb/flaskbb/cli/main.py
        # can't use current_app.root_path because it's not (yet) available
        config_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(__file__))
        )
        config_file = os.path.join(config_dir, "flaskbb.cfg")
        if os.path.exists(config_file):
                click.secho("[+] Found config file 'flaskbb.cfg' in {}"
                            .format(config_dir), fg="yellow")
                click.secho("[+] Using config from: {}".format(config_file),
                            fg="cyan")
        else:
            config_file = None
            click.secho("[~] Using default config.", fg="yellow")

    return create_app(config_file)


def set_config(ctx, param, value):
    """This will pass the config file to the create_app function."""
    ctx.ensure_object(ScriptInfo).config_file = value


@click.group(cls=FlaskGroup, create_app=make_app, add_version_option=False)
@click.option("--config", expose_value=False, callback=set_config,
              required=False, is_flag=False, is_eager=True, metavar="CONFIG",
              help="Specify the config to use in dotted module notation "
                   "e.g. flaskbb.configs.default.DefaultConfig")
@click.option("--version", expose_value=False, callback=get_version,
              is_flag=True, is_eager=True, help="Show the FlaskBB version.")
def flaskbb():
    """This is the commandline interface for flaskbb."""
    pass


flaskbb.add_command(alembic_click, "db")


@flaskbb.command()
@click.option("--welcome", "-w", default=True, is_flag=True,
              help="Disable the welcome forum.")
@click.option("--force", "-f", default=False, is_flag=True,
              help="Doesn't ask for confirmation.")
@click.option("--username", "-u", help="The username of the user.")
@click.option("--email", "-e", type=EmailType(),
              help="The email address of the user.")
@click.option("--password", "-p", help="The password of the user.")
def install(welcome, force, username, email, password):
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
        else:
            sys.exit(0)

    # creating database from scratch and 'stamping it'
    create_latest_db()

    click.secho("[+] Creating default settings...", fg="cyan")
    create_default_groups()
    create_default_settings()

    click.secho("[+] Creating admin user...", fg="cyan")
    prompt_save_user(username, email, password, "admin")

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
            create_latest_db()

    if initdb:
        click.secho("[+] Initializing database...", fg="cyan")
        create_latest_db()

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
        alembic.upgrade()

    if fixture or all_latest:
        try:
            settings = import_string(
                "flaskbb.fixtures.{}".format(fixture)
            )
            settings = settings.fixture
        except ImportError:
            raise FlaskBBCLIError("{} fixture is not available"
                                  .format(fixture), fg="red")

        click.secho("[+] Updating fixtures...", fg="cyan")
        count = update_settings_from_fixture(
            fixture=settings, overwrite_group=force, overwrite_setting=force
        )
        click.secho("[+] {} groups and {} settings updated.".format(
            len(count.keys()), len(count.values())), fg="green"
        )


@flaskbb.command("download-emojis")
@with_appcontext
def download_emoji():
    """Downloads emojis from emoji-cheat-sheet.com.
    This command is probably going to be removed in future version.
    """
    click.secho("[+] Downloading emojis...", fg="cyan")
    HOSTNAME = "https://api.github.com"
    REPO = "/repos/arvida/emoji-cheat-sheet.com/contents/public/graphics/emojis"  # noqa
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


@flaskbb.command("makeconfig")
@click.option("--development", "-d", default=False, is_flag=True,
              help="Creates a development config with DEBUG set to True.")
@click.option("--output", "-o", required=False,
              help="The path where the config file will be saved at. "
                   "Defaults to the flaskbb's root folder.")
@click.option("--force", "-f", default=False, is_flag=True,
              help="Overwrite any existing config file if one exists.")
def generate_config(development, output, force):
    """Generates a FlaskBB configuration file."""
    config_env = Environment(
        loader=FileSystemLoader(os.path.join(current_app.root_path, "configs"))
    )
    config_template = config_env.get_template('config.cfg.template')

    if output:
        config_path = os.path.abspath(output)
    else:
        config_path = os.path.dirname(current_app.root_path)

    if os.path.exists(config_path) and not os.path.isfile(config_path):
        config_path = os.path.join(config_path, "flaskbb.cfg")

    # An override to handle database location paths on Windows environments
    database_path = "sqlite:///" + os.path.join(os.path.dirname(current_app.instance_path), "flaskbb.sqlite")
    if os.name == 'nt':
        database_path = database_path.replace("\\", r"\\")

    default_conf = {
        "is_debug": True,
        "server_name": "localhost:5000",
        "url_scheme": "http",
        "database_uri": database_path,
        "redis_enabled": False,
        "redis_uri": "redis://localhost:6379",
        "mail_server": "localhost",
        "mail_port": 25,
        "mail_use_tls": False,
        "mail_use_ssl": False,
        "mail_username": "",
        "mail_password": "",
        "mail_sender_name": "FlaskBB Mailer",
        "mail_sender_address": "noreply@yourdomain",
        "mail_admin_address": "admin@yourdomain",
        "secret_key": binascii.hexlify(os.urandom(24)).decode(),
        "csrf_secret_key": binascii.hexlify(os.urandom(24)).decode(),
        "timestamp": datetime.utcnow().strftime("%A, %d. %B %Y at %H:%M")
    }

    if not force:
        config_path = prompt_config_path(config_path)

    if force and os.path.exists(config_path):
        click.secho("Overwriting existing config file: {}".format(config_path),
                    fg="yellow")

    if development:
        write_config(default_conf, config_template, config_path)
        sys.exit(0)

    # SERVER_NAME
    click.secho("The name and port number of the server.\n"
                "This is needed to correctly generate URLs when no request "
                "context is available.", fg="cyan")
    default_conf["server_name"] = click.prompt(
        click.style("Server Name", fg="magenta"), type=str,
        default=default_conf.get("server_name"))

    # PREFERRED_URL_SCHEME
    click.secho("The URL Scheme is also needed in order to generate correct "
                "URLs when no request context is available.\n"
                "Choose either 'https' or 'http'.", fg="cyan")
    default_conf["url_scheme"] = click.prompt(
        click.style("URL Scheme", fg="magenta"),
        type=click.Choice(["https", "http"]),
        default=default_conf.get("url_scheme"))

    # SQLALCHEMY_DATABASE_URI
    click.secho("For Postgres use:\n"
                "    postgresql://flaskbb@localhost:5432/flaskbb\n"
                "For more options see the SQLAlchemy docs:\n"
                "    http://docs.sqlalchemy.org/en/latest/core/engines.html",
                fg="cyan")
    default_conf["database_uri"] = click.prompt(
        click.style("Database URI", fg="magenta"),
        default=default_conf.get("database_uri"))

    # REDIS_ENABLED
    click.secho("Redis will be used for things such as the task queue, "
                "caching and rate limiting.", fg="cyan")
    default_conf["redis_enabled"] = click.confirm(
        click.style("Would you like to use redis?", fg="magenta"),
        default=True)  # default_conf.get("redis_enabled") is False

    # REDIS_URI
    if default_conf.get("redis_enabled", False):
        default_conf["redis_uri"] = click.prompt(
            click.style("Redis URI", fg="magenta"),
            default=default_conf.get("redis_uri"))
    else:
        default_conf["redis_uri"] = ""

    # MAIL_SERVER
    click.secho("To use 'localhost' make sure that you have sendmail or\n"
                "something similar installed. Gmail is also supprted.",
                fg="cyan")
    default_conf["mail_server"] = click.prompt(
        click.style("Mail Server", fg="magenta"),
        default=default_conf.get("mail_server"))
    # MAIL_PORT
    click.secho("The port on which the SMTP server is listening on.",
                fg="cyan")
    default_conf["mail_port"] = click.prompt(
        click.style("Mail Server SMTP Port", fg="magenta"),
        default=default_conf.get("mail_port"))
    # MAIL_USE_TLS
    click.secho("If you are using a local SMTP server like sendmail this is "
                "not needed. For external servers it is required.",
                fg="cyan")
    default_conf["mail_use_tls"] = click.confirm(
        click.style("Use TLS for sending mails?", fg="magenta"),
        default=default_conf.get("mail_use_tls"))
    # MAIL_USE_SSL
    click.secho("Same as above. TLS is the successor to SSL.", fg="cyan")
    default_conf["mail_use_ssl"] = click.confirm(
        click.style("Use SSL for sending mails?", fg="magenta"),
        default=default_conf.get("mail_use_ssl"))
    # MAIL_USERNAME
    click.secho("Not needed if you are using a local smtp server.\nFor gmail "
                "you have to put in your email address here.", fg="cyan")
    default_conf["mail_username"] = click.prompt(
        click.style("Mail Username", fg="magenta"),
        default=default_conf.get("mail_username"))
    # MAIL_PASSWORD
    click.secho("Not needed if you are using a local smtp server.\nFor gmail "
                "you have to put in your gmail password here.", fg="cyan")
    default_conf["mail_password"] = click.prompt(
        click.style("Mail Password", fg="magenta"),
        default=default_conf.get("mail_password"))
    # MAIL_DEFAULT_SENDER
    click.secho("The name of the sender. You probably want to change it to "
                "something like '<your_community> Mailer'.", fg="cyan")
    default_conf["mail_sender_name"] = click.prompt(
        click.style("Mail Sender Name", fg="magenta"),
        default=default_conf.get("mail_sender_name"))
    click.secho("On localhost you want to use a noreply address here. "
                "Use your email address for gmail here.", fg="cyan")
    default_conf["mail_sender_address"] = click.prompt(
        click.style("Mail Sender Address", fg="magenta"),
        default=default_conf.get("mail_sender_address"))
    # ADMINS
    click.secho("Logs and important system messages are sent to this address."
                "Use your email address for gmail here.", fg="cyan")
    default_conf["mail_admin_address"] = click.prompt(
        click.style("Mail Admin Email", fg="magenta"),
        default=default_conf.get("mail_admin_address"))

    write_config(default_conf, config_template, config_path)

    # Finished
    click.secho("The configuration file has been saved to:\n{cfg}\n"
                "Feel free to adjust it as needed."
                .format(cfg=config_path), fg="blue", bold=True)
    click.secho("Usage: \nflaskbb --config {cfg} run"
                .format(cfg=config_path), fg="green")
