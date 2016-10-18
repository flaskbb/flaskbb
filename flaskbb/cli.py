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

from flask.cli import FlaskGroup, with_appcontext
import click

from flaskbb import create_app


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """This is the commandline interface for flaskbb."""
    pass


@cli.command()
@click.option('--emojis', default=True, help='Downloads some emojis')
@click.option('--initdb', default=True, help='Creates an empty database')
@click.option('--dropdb', default=True, help='Deletes the database')
def install():
    """Installs flaskbb. If no arguments are used, an interactive setup
    will be run.
    """
    click.echo('FlaskBB has been successfully installed.')


@cli.command()
@click.option('--all', '-a', default=True, is_flag=True,
              help='Upgrades migrations AND fixtures to the latest version.')
@click.option('--fixture/', '-f', default=None,
              help='The fixture which should be upgraded or installed.')
@click.option('--force-fixture', '-ff', default=False, is_flag=True,
              help='Forcefully upgrades the fixtures.')
def upgrade(all, fixture, force_fixture):
    """Updates the migrations and fixtures."""
    click.echo('FlaskBB has been successfully installed.')


@cli.command()
@click.option('--test', '-t', default=False, is_flag=True,
              help='Adds some test data.')
@click.option('--posts', default=100,
              help='Number of posts to create in each topic (default: 100).')
@click.option('--topics', default=100,
              help='Number of topics to create (default: 100).')
@click.option('--force', '-f', default=100,
              help='Will delete the database before populating it.')
def populate(test, posts, topics):
    """Creates the necessary tables and groups for FlaskBB."""
    click.echo('populate()')


@cli.command()
@click.option("--server", "-s", type=click.Choice(["gunicorn"]))
def start(server):
    """Starts a production ready wsgi server.
    TODO: Unsure about this command, would 'serve' or 'server' be better?
    """
    click.echo('start()')


@cli.group()
def translations():
    """Translations command sub group."""
    click.echo('translations()')


@cli.group()
def plugins():
    """Plugins command sub group."""
    click.echo('plugins()')


@cli.group()
def themes():
    """Themes command sub group."""
    click.echo('themes()')


@cli.group()
def users():
    """Create, update or delete users."""
    click.echo("users()")


@users.command("new")
@click.option('--username', prompt=True,
              default=lambda: os.environ.get('USER', ''),
              help="The username of the new user.")
@click.option('--email', prompt=True,
              help="The email address of the new user.")
@click.option('--password', prompt=True, hide_input=True,
              confirmation_prompt=True,
              help="The password of the new user.")
def new_user(username, email, password):
    """Creates a new user. Omit any options to use the interactive mode."""
    click.echo('user: %s, %s, %s' % (username, email, password))


@cli.command('shell', short_help='Runs a shell in the app context.')
@with_appcontext
def shell_command():
    """Runs an interactive Python shell in the context of a given
    Flask application.  The application will populate the default
    namespace of this shell according to it's configuration.
    This is useful for executing small snippets of management code
    without having to manually configuring the application.

    This code snippet is taken from Flask's cli module and modified to
    run IPython and falls back to the normal shell if IPython is not
    available.
    """
    import code
    from flask import _app_ctx_stack
    app = _app_ctx_stack.top.app
    banner = 'Python %s on %s\nApp: %s%s\nInstance: %s' % (
        sys.version,
        sys.platform,
        app.import_name,
        app.debug and ' [debug]' or '',
        app.instance_path,
    )
    ctx = {}

    # Support the regular Python interpreter startup script if someone
    # is using it.
    startup = os.environ.get('PYTHONSTARTUP')
    if startup and os.path.isfile(startup):
        with open(startup, 'r') as f:
            eval(compile(f.read(), startup, 'exec'), ctx)

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
    column_headers = ('Rule', 'Endpoint', 'Arguments')

    rules = sorted(
        current_app.url_map.iter_rules(),
        key=lambda rule: getattr(rule, order)
    )
    for rule in rules:
        rows.append((rule.rule, rule.endpoint, None))
    column_length = 2

    str_template = ''
    table_width = 0

    if column_length >= 1:
        max_rule_length = max(len(r[0]) for r in rows)
        max_rule_length = max_rule_length if max_rule_length > 4 else 4
        str_template += '%-' + str(max_rule_length) + 's'
        table_width += max_rule_length

    if column_length >= 2:
        max_endpoint_len = max(len(str(r[1])) for r in rows)
        # max_endpoint_len = max(rows, key=len)
        max_endpoint_len = max_endpoint_len if max_endpoint_len > 8 else 8
        str_template += '  %-' + str(max_endpoint_len) + 's'
        table_width += 2 + max_endpoint_len

    if column_length >= 3:
        max_args_len = max(len(str(r[2])) for r in rows)
        max_args_len = max_args_len if max_args_len > 9 else 9
        str_template += '  %-' + str(max_args_len) + 's'
        table_width += 2 + max_args_len

    print(str_template % (column_headers[:column_length]))
    print('-' * table_width)

    for row in rows:
        print(str_template % row[:column_length])
