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
from flaskbb.extensions import db, plugin_manager, whooshee
from flaskbb.utils.populate import (create_test_data, create_welcome_forum,
                                    create_user, create_default_groups,
                                    create_default_settings, insert_bulk_data,
                                    update_settings_from_fixture)
from flaskbb.utils.translations import (add_translations,
                                        compile_translations,
                                        update_translations,
                                        add_plugin_translations,
                                        compile_plugin_translations,
                                        update_plugin_translations)

_email_regex = r"[^@]+@[^@]+\.[^@]+"


class EmailType(click.ParamType):
    """The choice type allows a value to be checked against a fixed set of
    supported values.  All of these values have to be strings.
    See :ref:`choice-opts` for an example.
    """
    name = 'email'

    def convert(self, value, param, ctx):
        # Exact match
        if re.match(_email_regex, value):
            return value
        else:
            self.fail(('invalid email: %s' % value), param, ctx)

    def __repr__(self):
        return 'email'


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
    if database_exists(db.engine.url):
        if click.confirm("Existing database found. Do you want to delete "
                         "the old one and create a new one?"):
            drop_database(db.engine.url)
            upgrade_database()
        else:
            sys.exit(0)
    else:
        upgrade_database()

    click.echo("Creating default settings...")
    create_default_groups()
    create_default_settings()

    click.echo("Creating user...")
    username = click.prompt(
        "Username", type=int, default=os.environ.get("USER", "")
    )
    email = click.prompt(
        "Email address", type=EmailType()
    )
    password = click.prompt(
        "Password", hide_input=True, confirmation_prompt=True
    )
    group = click.prompt(
        "Group", type=click.Choice(["admin", "super_mod", "mod", "member"]),
        default="admin"
    )
    create_user(username, password, email, group)

    if welcome_forum:
        click.echo("Creating welcome forum...")
        create_welcome_forum()

    click.echo("Compiling translations...")
    compile_translations()

    click.echo("FlaskBB has been successfully installed!")


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
        click.echo("Recreating database...")
        drop_database(db.engine.url)
        upgrade_database()

    if initdb:
        upgrade_database()

    if test_data:
        click.echo("Adding some test data...")
        create_test_data()

    if bulk_data:
        timer = time.time()
        topic_count, post_count = insert_bulk_data(int(topics), int(posts))
        elapsed = time.time() - timer
        click.echo("It took {} seconds to create {} topics and {} posts"
                   .format(elapsed, topic_count, post_count))


@cli.group()
def translations():
    """Translations command sub group."""
    pass


@cli.group()
def plugins():
    """Plugins command sub group."""
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

        click.echo("[+] User {} with Email {} in Group {} created.".format(
            user.username, user.email, user.primary_group.name)
        )
    except IntegrityError:
        click.Abort("Couldn't create the user because the username or "
                    "email address is already taken.")


@cli.command()
def reindex():
    """Reindexes the search index."""
    click.echo("Reindexing search index...")
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
    click.echo("FlaskBB has been successfully upgraded.")


@cli.command()
@click.option("--server", "-s", type=click.Choice(["gunicorn"]))
def start(server):
    """Starts a production ready wsgi server.
    TODO: Unsure about this command, would "serve" or "server" be better?
    """
    click.echo("start()")


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
    banner = "Python %s on %s\nApp: %s%s\nInstance: %s" % (
        sys.version,
        sys.platform,
        app.import_name,
        app.debug and " [debug]" or "",
        app.instance_path,
    )
    ctx = {}

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
