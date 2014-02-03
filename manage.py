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
from flask import current_app
from flask.ext.script import Manager, Shell, Server, prompt, prompt_pass
from flask.ext.migrate import MigrateCommand

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
def createall():
    """Creates the database with some testing content."""

    # Just for testing purposes
    db.drop_all()

    db.create_all()
    create_test_data()


@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
@manager.option('-e', '--email', dest='email')
def create_admin(username, password, email):
    """Creates the admin user"""

    username = prompt("Username")
    email = prompt("A valid email address")
    password = prompt_pass("Password")

    create_admin_user(username, email, password)


@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
@manager.option('-e', '--email', dest='email')
@manager.option('-d', '--dropdb', dest='dropdb', default=False)
def initflaskbb(username, password, email, dropdb=False):
    """Initializes FlaskBB with all necessary data"""

    if dropdb:
        app.logger.info("Dropping previous database...")
        db.drop_all()

    app.logger.info("Creating tables...")
    db.create_all()

    app.logger.info("Creating default groups...")
    create_default_groups()

    app.logger.info("Creating admin user...")
    create_admin(username, password, email)

    app.logger.info("Creating welcome forum...")
    create_welcome_forum()

    app.logger.info("Congratulations! FlaskBB has been successfully installed")


if __name__ == "__main__":
    manager.run()
