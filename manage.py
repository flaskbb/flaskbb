#!/usr/bin/env python

"""
    flaskbb.manage
    ~~~~~~~~~~~~~~~~~~~~

    This script provides some easy to use commands for
    creating the database with or without some sample content.
    You can also run the development server with it.
    Just type `python manage.py` to see the full list of commands.

    TODO: When Flask 1.0 is released, get rid of Flask-Script and use click.
          Then it's also possible to split the commands in "command groups"
          which would make the commands better seperated from each other
          and less confusing.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
import subprocess

from flask import current_app
from werkzeug.utils import import_string
from sqlalchemy.exc import IntegrityError, OperationalError
from flask_script import (Manager, Shell, Server, prompt, prompt_pass,
                          prompt_bool)
from flask_migrate import MigrateCommand, upgrade

from flaskbb import create_app
from flaskbb.extensions import db, plugin_manager
from flaskbb.utils.populate import (create_test_data, create_welcome_forum,
                                    create_admin_user, create_default_groups,
                                    create_default_settings, insert_mass_data,
                                    update_settings_from_fixture)

# Use the development configuration if available
try:
    from flaskbb.configs.development import DevelopmentConfig as Config
except ImportError:
    from flaskbb.configs.default import DefaultConfig as Config

app = create_app(Config)
manager = Manager(app)

# Used to get the plugin translations
PLUGINS_FOLDER = os.path.join(app.root_path, "plugins")

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

    upgrade()


@manager.command
def dropdb():
    """Deletes the database."""

    db.drop_all()


@manager.command
def populate(dropdb=False, createdb=False):
    """Creates the database with some default data.
    If you do not want to drop or create the db add
    '-c' (to not create the db) and '-d' (to not drop the db)
    """

    if not dropdb:
        app.logger.info("Dropping database...")
        db.drop_all()

    if not createdb:
        app.logger.info("Creating database...")
        upgrade()

    app.logger.info("Creating test data...")
    create_test_data()


@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
@manager.option('-e', '--email', dest='email')
def create_admin(username=None, password=None, email=None):
    """Creates the admin user."""

    if not (username and password and email):
        username = prompt("Username")
        email = prompt("A valid email address")
        password = prompt_pass("Password")

    create_admin_user(username=username, password=password, email=email)


@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
@manager.option('-e', '--email', dest='email')
def init(username=None, password=None, email=None):
    """Initializes FlaskBB with all necessary data."""

    app.logger.info("Creating default data...")
    try:
        create_default_groups()
        create_default_settings()
    except IntegrityError:
        app.logger.error("Couldn't create the default data because it already "
                         "exist!")
        if prompt_bool("Found an existing database."
                       "Do you want to recreate the database? (y/n)"):
            db.session.rollback()
            db.drop_all()
            upgrade()
            create_default_groups()
            create_default_settings()
        else:
            sys.exit(0)
    except OperationalError:
        app.logger.error("No database found.")
        if prompt_bool("Do you want to create the database now? (y/n)"):
            db.session.rollback()
            upgrade()
            create_default_groups()
            create_default_settings()
        else:
            sys.exit(0)

    app.logger.info("Creating admin user...")
    if username and password and email:
        create_admin_user(username=username, password=password, email=email)
    else:
        create_admin()

    app.logger.info("Creating welcome forum...")
    create_welcome_forum()

    app.logger.info("Compiling translations...")
    compile_translations()

    app.logger.info("Congratulations! FlaskBB has been successfully installed")


@manager.command
def insertmassdata():
    """Warning: This can take a long time!.
    Creates 100 topics and each topic contains 100 posts.
    """
    insert_mass_data()


@manager.option('-s', '--settings', dest="settings")
@manager.option('-f', '--force', dest="force", default=False)
def update(settings=None, force=False):
    """Updates the settings via a fixture. All fixtures have to be placed
    in the `fixture`.
    Usage: python manage.py update -s your_fixture
    """

    try:
        fixture = import_string(
            "flaskbb.fixtures.{}".format(settings)
        )
        fixture = fixture.fixture
    except ImportError:
        raise "{} fixture is not available".format(settings)

    if force:
        count = update_settings_from_fixture(fixture, overwrite_group=True,
                                             overwrite_setting=True)
        app.logger.info(
            "{} groups and {} settings forcefully updated."
            .format(count[0], count[1])
        )
    else:
        count = update_settings_from_fixture(fixture)
        app.logger.info(
            "{} groups and {} settings updated.".format(count[0], count[1])
        )


@manager.command
def update_translations():
    """Updates all translations."""

    # update flaskbb translations
    translations_folder = os.path.join(app.root_path, "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(["pybabel", "extract", "-F", "babel.cfg",
                     "-k", "lazy_gettext", "-o", source_file, "."])
    subprocess.call(["pybabel", "update", "-i", source_file,
                     "-d", translations_folder])

    # updates all plugin translations too
    for plugin in plugin_manager.all_plugins:
        update_plugin_translations(plugin)


@manager.command
def add_translations(translation):
    """Adds a new language to the translations."""

    translations_folder = os.path.join(app.root_path, "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(["pybabel", "extract", "-F", "babel.cfg",
                     "-k", "lazy_gettext", "-o", source_file, "."])
    subprocess.call(["pybabel", "init", "-i", source_file,
                     "-d", translations_folder, "-l", translation])


@manager.command
def compile_translations():
    """Compiles all translations."""

    # compile flaskbb translations
    translations_folder = os.path.join(app.root_path, "translations")
    subprocess.call(["pybabel", "compile", "-d", translations_folder])

    # compile all plugin translations
    for plugin in plugin_manager.all_plugins:
        compile_plugin_translations(plugin)


# Plugin translation commands
@manager.command
def add_plugin_translations(plugin, translation):
    """Adds a new language to the plugin translations. Expects the name
    of the plugin and the translations name like "en".
    """

    plugin_folder = os.path.join(PLUGINS_FOLDER, plugin)
    translations_folder = os.path.join(plugin_folder, "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(["pybabel", "extract", "-F", "babel.cfg",
                     "-k", "lazy_gettext", "-o", source_file,
                     plugin_folder])
    subprocess.call(["pybabel", "init", "-i", source_file,
                     "-d", translations_folder, "-l", translation])


@manager.command
def update_plugin_translations(plugin):
    """Updates the plugin translations. Expects the name of the plugin."""

    plugin_folder = os.path.join(PLUGINS_FOLDER, plugin)
    translations_folder = os.path.join(plugin_folder, "translations")
    source_file = os.path.join(translations_folder, "messages.pot")

    subprocess.call(["pybabel", "extract", "-F", "babel.cfg",
                     "-k", "lazy_gettext", "-o", source_file,
                     plugin_folder])
    subprocess.call(["pybabel", "update", "-i", source_file,
                     "-d", translations_folder])


@manager.command
def compile_plugin_translations(plugin):
    """Compile the plugin translations. Expects the name of the plugin."""

    plugin_folder = os.path.join(PLUGINS_FOLDER, plugin)
    translations_folder = os.path.join(plugin_folder, "translations")

    subprocess.call(["pybabel", "compile", "-d", translations_folder])


if __name__ == "__main__":
    manager.run()
