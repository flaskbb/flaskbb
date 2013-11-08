"""
    flaskbb.manage
    ~~~~~~~~~~~~~~~~~~~~

    This script provides some easy to use commands for
    creating the database with or without some sample content.
    You can also run the development server with it.
    Just type `python manage.py` to see the full list of commands.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import os

from flask import current_app
from flask.ext.script import Manager, Shell, Server

from flaskbb import create_app
from flaskbb.extensions import db
from flaskbb.utils.populate import (create_test_data, create_admin_user,
                                    create_welcome_forum, create_default_groups)

# Use the development configuration if available
try:
    from flaskbb.configs.development import DevelopmentConfig as Config
except ImportError:
    from flaskbb.configs.default import DefaultConfig as Config

app = create_app(Config)
manager = Manager(app)

# Run local server
manager.add_command("runserver", Server("localhost", port=8080))


# Add interactive project shell
def make_shell_context():
    return dict(app=current_app, db=db)
manager.add_command("shell", Shell(make_context=make_shell_context))


@manager.command
def initdb():
    """
    Creates the database.
    """

    db.create_all()


@manager.command
def createall():
    """
    Creates the database with some example content.
    """

    # Just for testing purposes
    dbfile = os.path.join(Config._basedir, "flaskbb.sqlite")
    if os.path.exists(dbfile):
        os.remove(dbfile)

    db.create_all()
    create_test_data()


@manager.command
def create_admin():
    """
    Creates the admin user
    """
    db.create_all()
    create_admin_user()


@manager.command
def create_default_data():
    """
    This should be created by every flaskbb installation
    """
    db.create_all()
    create_default_groups()
    create_welcome_forum()


if __name__ == "__main__":
    manager.run()
