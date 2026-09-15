"""
flaskbb.cli.plugins
~~~~~~~~~~~~~~~~~~~

This module contains all plugin commands.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import click
import flask_alembic.cli as alembic_cli
from alembic.script.revision import ResolutionError
from flask import current_app
from flask.cli import with_appcontext

from flaskbb.cli.main import flaskbb
from flaskbb.utils.alembic import Alembic


@flaskbb.group()
@with_appcontext
@click.pass_context
def db(ctx: click.Context):
    """Database command sub group. Wraps Flask-Alembic's CLI for running
    migrations, with branch-per-plugin support (e.g. ``flaskbb db revision
    --branch <plugin_name>``)."""
    ctx.obj = current_app.extensions["alembic"]


def _is_revision_id(alembic: Alembic, target: str) -> bool:
    # alembic also resolves unique prefixes, "9" would find 933bd7d807c4
    try:
        revision = alembic.script_directory.revision_map.get_revision(target)
    except ResolutionError:
        return False
    return revision is not None and revision.revision == target


@db.command()
@click.pass_obj
@click.argument("target", default="-1")
def downgrade(alembic: Alembic, target: str = "-1"):
    """Run migrations to downgrade the database."""
    # Flask-Alembic's downgrade reads every number as the count of revisions
    # to go back, but FlaskBB's revision ids are numbers (timestamps) as well
    try:
        steps = int(target)
    except ValueError:
        pass
    else:
        if not _is_revision_id(alembic, target):
            target = str(-abs(steps))

    alembic.downgrade(target)


db.add_command(alembic_cli.mkdir)
db.add_command(alembic_cli.current)
db.add_command(alembic_cli.heads)
db.add_command(alembic_cli.branches)
db.add_command(alembic_cli.log)
db.add_command(alembic_cli.show)
db.add_command(alembic_cli.check)
db.add_command(alembic_cli.stamp)
db.add_command(alembic_cli.upgrade)
db.add_command(alembic_cli.revision)
db.add_command(alembic_cli.merge)
