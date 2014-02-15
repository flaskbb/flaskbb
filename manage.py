"""
    flaskbb.manage
    ~~~~~~~~~~~~~~~~~~~~

    This script provides some easy to use commands for
    creating the database with or without some sample content.
    You can also run the development server with it.
    Just type `python manage.py` to see the full list of commands.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys

from flask import current_app
from sqlalchemy.exc import IntegrityError, OperationalError
from flask.ext.script import (Manager, Shell, Server, prompt, prompt_pass,
                              prompt_bool)
from flask.ext.migrate import MigrateCommand, upgrade as db_upgrade

from flaskbb import create_app
from flaskbb.extensions import db
from flaskbb.utils.populate import (create_test_data, create_welcome_forum,
                                    create_admin_user, create_default_groups)

# Use the development configuration if available
try:
    from flaskbb.configs.development import DevelopmentConfig as Config
except ImportError:
    from flaskbb.configs.default import DefaultConfig as Config

app = create_app(Config)
manager = Manager(app)

# Run local server
manager.add_command("runserver", Server("localhost", port=8080))

# Migration commands
manager.add_command('db', MigrateCommand)


# Add interactive project shell
def make_shell_context():
    return dict(app=current_app, db=db)
manager.add_command("shell", Shell(make_context=make_shell_context))


@manager.command
def initdb():
    """Creates the database."""

    db.create_all()


@manager.command
def dropdb():
    """Deletes the database"""

    db.drop_all()


@manager.command
def createall(dropdb=False, createdb=False):
    """Creates the database with some testing content.
    If you do not want to drop or create the db add
    '-c' (to not create the db) and '-d' (to not drop the db)
    """

    if not dropdb:
        app.logger.info("Dropping database...")
        db.drop_all()

    if not createdb:
        app.logger.info("Creating database...")
        db.create_all()

    app.logger.info("Creating test data...")
    create_test_data()


@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
@manager.option('-e', '--email', dest='email')
def create_admin(username=None, password=None, email=None):
    """Creates the admin user"""

    if not (username and password and email):
        username = prompt("Username")
        email = prompt("A valid email address")
        password = prompt_pass("Password")

    create_admin_user(username=username, password=password, email=email)


@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
@manager.option('-e', '--email', dest='email')
def initflaskbb(username=None, password=None, email=None):
    """Initializes FlaskBB with all necessary data"""

    app.logger.info("Creating default groups...")
    try:
        create_default_groups()
    except IntegrityError:
        app.logger.error("Couldn't create the default groups because they are already exist!")
        if prompt_bool("Do you want to recreate the database? (y/n)"):
            db.session.rollback()
            db.drop_all()
            db.create_all()
            create_default_groups()
        else:
            sys.exit(0)
    except OperationalError:
        app.logger.error("No database found.")
        if prompt_bool("Do you want to create the database? (y/n)"):
            db.session.rollback()
            db.create_all()
            create_default_groups()
        else:
            sys.exit(0)

    app.logger.info("Creating admin user...")
    if username and password and email:
        create_admin_user(username=username, password=password, email=email)
    else:
        create_admin()

    app.logger.info("Creating welcome forum...")
    create_welcome_forum()

    app.logger.info("Congratulations! FlaskBB has been successfully installed")


if __name__ == "__main__":
    manager.run()
