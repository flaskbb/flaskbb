"""
flaskbb.cli.plugins
~~~~~~~~~~~~~~~~~~~

This module contains all plugin commands.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import click
import flask_alembic.cli as alembic_cli
from flask import current_app
from flask.cli import with_appcontext

from flaskbb.cli.main import flaskbb


@flaskbb.group()
@with_appcontext
@click.pass_context
def db(ctx: click.Context):
    """Database command sub group. Wraps Flask-Alembic's CLI for running
    migrations, with branch-per-plugin support (e.g. ``flaskbb db revision
    --branch <plugin_name>``)."""
    ctx.obj = current_app.extensions["alembic"]


db.add_command(alembic_cli.mkdir)
db.add_command(alembic_cli.current)
db.add_command(alembic_cli.heads)
db.add_command(alembic_cli.branches)
db.add_command(alembic_cli.log)
db.add_command(alembic_cli.show)
db.add_command(alembic_cli.check)
db.add_command(alembic_cli.stamp)
db.add_command(alembic_cli.upgrade)
db.add_command(alembic_cli.downgrade)
db.add_command(alembic_cli.revision)
db.add_command(alembic_cli.merge)
