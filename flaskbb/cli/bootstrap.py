"""
flaskbb.cli.bootstrap
~~~~~~~~~~~~~~~~~~~~~

Prepares the database before FlaskBB starts, e.g. in a container entrypoint.

:copyright: (c) 2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import subprocess
import sys
import time

import click
import sqlalchemy as sa
from flask.cli import with_appcontext
from sqlalchemy.exc import OperationalError

from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import FlaskBBCLIError
from flaskbb.extensions import db
from flaskbb.plugins.models import PluginRegistry
from flaskbb.user.models import User
from flaskbb.utils.proxies import current_app

INSTALL_HINT = """\
The database is empty and no administrator credentials were provided.
Pass --username, --email and --password (or set ADMIN_USERNAME, ADMIN_EMAIL
and ADMIN_PASSWORD), or install FlaskBB interactively with 'flaskbb install'."""


@flaskbb.command()
@click.option("--wait-only", is_flag=True, help="Only wait for the database.")
@click.option(
    "--timeout",
    default=60,
    show_default=True,
    envvar="FLASKBB_DB_TIMEOUT",
    help="Seconds to wait for the database.",
)
@click.option("--username", envvar="ADMIN_USERNAME", help="The administrator created on install.")
@click.option("--email", envvar="ADMIN_EMAIL", help="The administrator's email address.")
@click.option("--password", envvar="ADMIN_PASSWORD", help="The administrator's password.")
@click.option(
    "--enable-plugins",
    envvar="FLASKBB_ENABLE_PLUGINS",
    default="",
    help="Comma separated plugins to enable and install unless they are enabled.",
)
@with_appcontext
def bootstrap(
    wait_only: bool,
    timeout: int,
    username: str | None,
    email: str | None,
    password: str | None,
    enable_plugins: str,
):
    """Waits for the database and then installs FlaskBB into an empty
    database or migrates an existing one, and enables the given plugins.
    Safe to run before every start of FlaskBB.
    """
    wait_for_database(timeout)
    if wait_only:
        return

    if is_installed():
        # also applies the new migrations of every enabled plugin
        run_flaskbb("Migrating the database", "db", "upgrade")
    elif username and email and password:
        run_flaskbb(
            "The database is empty, installing FlaskBB",
            "install",
            "--force",
            "--username",
            username,
            "--email",
            email,
            "--password",
            password,
        )
    else:
        raise FlaskBBCLIError(INSTALL_HINT, fg="red")

    names = [name.strip() for name in enable_plugins.split(",") if name.strip()]
    with db.engine.connect() as connection:
        enabled = set(
            connection.scalars(sa.select(PluginRegistry.name).where(PluginRegistry.enabled))
        )
    for name in names:
        if name not in enabled:
            run_flaskbb(f"Enabling plugin '{name}'", "plugins", "enable", name)
            run_flaskbb(f"Installing plugin '{name}'", "plugins", "install", name)


def wait_for_database(timeout: int):
    deadline = time.monotonic() + timeout
    while True:
        try:
            with db.engine.connect():
                return
        except OperationalError as exc:
            if time.monotonic() >= deadline:
                raise FlaskBBCLIError(
                    f"The database isn't reachable after {timeout}s: {exc}", fg="red"
                ) from exc
            click.secho("[+] Waiting for the database...", fg="cyan")
            time.sleep(2)


def is_installed() -> bool:
    # an install that failed halfway leaves the tables behind, but no user
    if not sa.inspect(db.engine).has_table(User.__tablename__):
        return False
    with db.engine.connect() as connection:
        return connection.scalar(sa.select(User.id).limit(1)) is not None


def run_flaskbb(description: str, *args: str):
    # Every step gets a fresh process: this app may have been created before
    # the database was reachable, and a plugin is only loaded by an app that
    # was created after it got enabled. The arguments aren't logged, they
    # can contain the admin password.
    options = ["--instance", current_app.instance_path]
    if isinstance(current_app.config["CONFIG_PATH"], str):
        options += ["--config", current_app.config["CONFIG_PATH"]]

    click.secho(f"[+] {description}...", fg="cyan")
    try:
        subprocess.run([sys.executable, "-m", "flaskbb", *options, *args], check=True)
    except subprocess.CalledProcessError as exc:
        raise FlaskBBCLIError(f"{description} failed.", fg="red") from exc
