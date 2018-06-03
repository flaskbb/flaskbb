# -*- coding: utf-8 -*-
"""
    flaskbb.cli.commands
    ~~~~~~~~~~~~~~~~~~~~

    This module contains the main commands.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import binascii
import logging
import os
import sys
import time
import traceback
from datetime import datetime

import click
import click_log
from celery.bin.celery import CeleryCommand
from flask import current_app
from flask.cli import FlaskGroup, ScriptInfo, with_appcontext
from flask_alembic import alembic_click
from jinja2 import Environment, FileSystemLoader
from sqlalchemy_utils.functions import database_exists
from werkzeug.utils import import_string

from flaskbb import create_app
from flaskbb.cli.utils import (EmailType, FlaskBBCLIError, get_version,
                               prompt_config_path, prompt_save_user,
                               write_config)
from flaskbb.extensions import alembic, celery, db, whooshee
from flaskbb.utils.populate import (create_default_groups,
                                    create_default_settings, create_latest_db,
                                    create_test_data, create_welcome_forum,
                                    insert_bulk_data, run_plugin_migrations,
                                    update_settings_from_fixture)
from flaskbb.utils.translations import compile_translations


logger = logging.getLogger(__name__)
click_log.basic_config(logger)


class FlaskBBGroup(FlaskGroup):
    def __init__(self, *args, **kwargs):
        super(FlaskBBGroup, self).__init__(*args, **kwargs)
        self._loaded_flaskbb_plugins = False

    def _load_flaskbb_plugins(self, ctx):
        if self._loaded_flaskbb_plugins:
            return

        try:
            app = ctx.ensure_object(ScriptInfo).load_app()
            app.pluggy.hook.flaskbb_cli(cli=self, app=app)
            self._loaded_flaskbb_plugins = True
        except Exception:
            logger.error(
                "Error while loading CLI Plugins",
                exc_info=traceback.format_exc()
            )
        else:
            shell_context_processors = app.pluggy.hook.flaskbb_shell_context()
            for p in shell_context_processors:
                app.shell_context_processor(p)

    def get_command(self, ctx, name):
        self._load_flaskbb_plugins(ctx)
        return super(FlaskBBGroup, self).get_command(ctx, name)

    def list_commands(self, ctx):
        self._load_flaskbb_plugins(ctx)
        return super(FlaskBBGroup, self).list_commands(ctx)


def make_app(script_info):
    config_file = getattr(script_info, "config_file", None)
    instance_path = getattr(script_info, "instance_path", None)
    return create_app(config_file, instance_path)


def set_config(ctx, param, value):
    """This will pass the config file to the create_app function."""
    ctx.ensure_object(ScriptInfo).config_file = value


def set_instance(ctx, param, value):
    """This will pass the instance path on the script info which can then
    be used in 'make_app'."""
    ctx.ensure_object(ScriptInfo).instance_path = value


@click.group(cls=FlaskBBGroup, create_app=make_app, add_version_option=False,
             invoke_without_command=True)
@click.option("--config", expose_value=False, callback=set_config,
              required=False, is_flag=False, is_eager=True, metavar="CONFIG",
              help="Specify the config to use either in dotted module "
                   "notation e.g. 'flaskbb.configs.default.DefaultConfig' "
                   "or by using a path like '/path/to/flaskbb.cfg'")
@click.option("--instance", expose_value=False, callback=set_instance,
              required=False, is_flag=False, is_eager=True, metavar="PATH",
              help="Specify the instance path to use. By default the folder "
                   "'instance' next to the package or module is assumed to "
                   "be the instance path.")
@click.option("--version", expose_value=False, callback=get_version,
              is_flag=True, is_eager=True, help="Show the FlaskBB version.")
@click.pass_context
@click_log.simple_verbosity_option(logger)
def flaskbb(ctx):
    """This is the commandline interface for flaskbb."""
    if ctx.invoked_subcommand is None:
        # show the help text instead of an error
        # when just '--config' option has been provided
        click.echo(ctx.get_help())


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
@click.option("--no-plugins", "-n", default=False, is_flag=True,
              help="Don't run the migrations for the default plugins.")
@with_appcontext
def install(welcome, force, username, email, password, no_plugins):
    """Installs flaskbb. If no arguments are used, an interactive setup
    will be run.
    """
    click.secho("[+] Installing FlaskBB...", fg="cyan")
    if database_exists(db.engine.url):
        if force or click.confirm(click.style(
            "Existing database found. Do you want to delete the old one and "
            "create a new one?", fg="magenta")
        ):
            db.drop_all()
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

    if not no_plugins:
        click.secho("[+] Installing default plugins...", fg="cyan")
        run_plugin_migrations()

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
        db.drop_all()

        # do not initialize the db if -i is passed
        if not initdb:
            create_latest_db()

    if initdb:
        click.secho("[+] Initializing database...", fg="cyan")
        create_latest_db()
        run_plugin_migrations()

    if test_data:
        click.secho("[+] Adding some test data...", fg="cyan")
        create_test_data()

    if bulk_data:
        click.secho("[+] Adding a lot of test data...", fg="cyan")
        timer = time.time()
        rv = insert_bulk_data(int(topics), int(posts))
        if not rv and not test_data:
            create_test_data()
            rv = insert_bulk_data(int(topics), int(posts))
        elapsed = time.time() - timer
        click.secho("[+] It took {:.2f} seconds to create {} topics and {} "
                    "posts.".format(elapsed, rv[0], rv[1]), fg="cyan")

    # this just makes the most sense for the command name; use -i to
    # init the db as well
    if not test_data and not bulk_data:
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
        click.secho("[+] {settings} settings in {groups} setting groups "
                    "updated.".format(groups=len(count), settings=sum(
                        len(settings) for settings in count.values())
                    ), fg="green")


@flaskbb.command("celery", add_help_option=False,
                 context_settings={"ignore_unknown_options": True,
                                   "allow_extra_args": True})
@click.pass_context
@with_appcontext
def start_celery(ctx):
    """Preconfigured wrapper around the 'celery' command."""
    CeleryCommand(celery).execute_from_commandline(
        ["flaskbb celery"] + ctx.args
    )


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
    database_path = "sqlite:///" + os.path.join(
        os.path.dirname(current_app.instance_path), "flaskbb.sqlite")
    if os.name == 'nt':
        database_path = database_path.replace("\\", r"\\")

    default_conf = {
        "is_debug": False,
        "server_name": "example.org",
        "use_https": True,
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
        "timestamp": datetime.utcnow().strftime("%A, %d. %B %Y at %H:%M"),
        "log_config_path": "",
        "deprecation_level": "default"
    }

    if not force:
        config_path = prompt_config_path(config_path)

    if force and os.path.exists(config_path):
        click.secho("Overwriting existing config file: {}".format(config_path),
                    fg="yellow")

    if development:
        default_conf["is_debug"] = True
        default_conf["use_https"] = False
        default_conf["server_name"] = "localhost:5000"
        write_config(default_conf, config_template, config_path)
        sys.exit(0)

    # SERVER_NAME
    click.secho("The name and port number of the exposed server.\n"
                "If FlaskBB is accesible on port 80 you can just omit the "
                "port.\n For example, if FlaskBB is accessible via "
                "example.org:8080 than this is also what you would set here.",
                fg="cyan")
    default_conf["server_name"] = click.prompt(
        click.style("Server Name", fg="magenta"), type=str,
        default=default_conf.get("server_name"))

    # HTTPS or HTTP
    click.secho("Is HTTPS (recommended) or HTTP used for to serve FlaskBB?",
                fg="cyan")
    default_conf["use_https"] = click.confirm(
        click.style("Use HTTPS?", fg="magenta"),
        default=default_conf.get("use_https"))

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
    click.secho("Logs and important system messages are sent to this address. "
                "Use your email address for gmail here.", fg="cyan")
    default_conf["mail_admin_address"] = click.prompt(
        click.style("Mail Admin Email", fg="magenta"),
        default=default_conf.get("mail_admin_address"))

    click.secho("Optional filepath to load a logging configuration file from. "
                "See the Python logging documentation for more detail.\n"
                "\thttps://docs.python.org/library/logging.config.html#logging-config-fileformat",  # noqa
                fg="cyan")
    default_conf["log_config_path"] = click.prompt(
        click.style("Logging Config Path", fg="magenta"),
        default=default_conf.get("log_config_path"))

    deprecation_mesg = (
        "Warning level for deprecations. options are: \n"
        "\terror\tturns deprecation warnings into exceptions\n"
        "\tignore\tnever warns about deprecations\n"
        "\talways\talways warns about deprecations even if the warning has been issued\n"  # noqa
        "\tdefault\tshows deprecation warning once per usage\n"
        "\tmodule\tshows deprecation warning once per module\n"
        "\tonce\tonly shows deprecation warning once regardless of location\n"
        "If you are unsure, select default\n"
        "for more details see: https://docs.python.org/3/library/warnings.html#the-warnings-filter"  # noqa
    )

    click.secho(deprecation_mesg, fg="cyan")
    default_conf["deprecation_level"] = click.prompt(
        click.style("Deperecation warning level", fg="magenta"),
        default=default_conf.get("deprecation_level")
    )

    write_config(default_conf, config_template, config_path)

    # Finished
    click.secho("The configuration file has been saved to:\n{cfg}\n"
                "Feel free to adjust it as needed."
                .format(cfg=config_path), fg="blue", bold=True)
    click.secho("Usage: \nflaskbb --config {cfg} run"
                .format(cfg=config_path), fg="green")
