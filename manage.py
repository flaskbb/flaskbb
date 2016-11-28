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
from __future__ import print_function
import sys
import os
import subprocess
import requests
import time

from flask import current_app
from werkzeug.utils import import_string
from sqlalchemy.exc import IntegrityError, OperationalError
from flask_script import (Manager, Shell, Server, prompt, prompt_pass,
                          prompt_bool)
from flask_migrate import MigrateCommand, upgrade

from flaskbb import create_app
from flaskbb.extensions import db, plugin_manager, whooshee
from flaskbb.utils.populate import (create_test_data, create_welcome_forum,
                                    create_admin_user, create_default_groups,
                                    create_default_settings, insert_bulk_data,
                                    update_settings_from_fixture)

# Use the development configuration if available
try:
    from flaskbb.configs.development import DevelopmentConfig as Config
except ImportError:
    try:
        from flaskbb.configs.production import ProductionConfig as Config
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
def initdb(default_settings=True):
    """Creates the database."""
    upgrade()

    if default_settings:
        print("Creating default data...")
        create_default_groups()
        create_default_settings()


@manager.command
def dropdb():
    """Deletes the database."""
    db.drop_all()


@manager.command
def populate(dropdb=False, createdb=False):
    """Creates the database with some default data.
    To drop or create the databse use the '-d' or '-c' options.
    """
    if dropdb:
        print("Dropping database...")
        db.drop_all()

    if createdb:
        print("Creating database...")
        upgrade()

    print("Creating test data...")
    create_test_data()


@manager.command
def reindex():
    """Reindexes the search index."""
    print("Reindexing search index...")
    whooshee.reindex()


@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
@manager.option('-e', '--email', dest='email')
def create_admin(username=None, password=None, email=None):
    """Creates the admin user."""

    if not (username and password and email):
        username = unicode(prompt("Username"))
        email = unicode(prompt("A valid email address"))
        password = unicode(prompt_pass("Password"))

    create_admin_user(username=username, password=password, email=email)


@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
@manager.option('-e', '--email', dest='email')
def install(username=None, password=None, email=None):
    """Installs FlaskBB with all necessary data."""

    print("Creating default data...")
    try:
        create_default_groups()
        create_default_settings()
    except IntegrityError:
        print("Couldn't create the default data because it already exist!")
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
        print("No database found.")
        if prompt_bool("Do you want to create the database now? (y/n)"):
            db.session.rollback()
            upgrade()
            create_default_groups()
            create_default_settings()
        else:
            sys.exit(0)

    print("Creating admin user...")
    if username and password and email:
        create_admin_user(username=username, password=password, email=email)
    else:
        create_admin()

    print("Creating welcome forum...")
    create_welcome_forum()

    print("Compiling translations...")
    compile_translations()

    if prompt_bool("Do you want to use Emojis? (y/n)"):
        print("Downloading emojis. This can take a few minutes.")
        download_emoji()

    print("Congratulations! FlaskBB has been successfully installed")


@manager.option('-t', '--topics', dest="topics", default=100)
@manager.option('-p', '--posts', dest="posts", default=100)
def insertbulkdata(topics, posts):
    """Warning: This can take a long time!.
    Creates 100 topics and each topic contains 100 posts.
    """
    timer = time.time()
    created_topics, created_posts = insert_bulk_data(int(topics), int(posts))
    elapsed = time.time() - timer

    print("It took {time} seconds to create {topics} topics and "
          "{posts} posts"
          .format(time=elapsed, topics=created_topics, posts=created_posts))


@manager.option('-f', '--force', dest="force", default=False)
@manager.option('-s', '--settings', dest="settings")
def update(settings=None, force=False):
    """Updates the settings via a fixture. All fixtures have to be placed
    in the `fixture`.
    Usage: python manage.py update -s your_fixture
    """
    if settings is None:
        settings = "settings"

    try:
        fixture = import_string(
            "flaskbb.fixtures.{}".format(settings)
        )
        fixture = fixture.fixture
    except ImportError:
        raise "{} fixture is not available".format(settings)

    overwrite_group = overwrite_setting = False
    if force:
        overwrite_group = overwrite_setting = True

    count = update_settings_from_fixture(
        fixture=fixture,
        overwrite_group=overwrite_group,
        overwrite_setting=overwrite_setting
    )
    print("{} groups and {} settings updated.".format(
        len(count.keys()), len(count.values()))
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


@manager.command
def download_emoji():
    """Downloads emojis from emoji-cheat-sheet.com."""
    HOSTNAME = "https://api.github.com"
    REPO = "/repos/arvida/emoji-cheat-sheet.com/contents/public/graphics/emojis"
    FULL_URL = "{}{}".format(HOSTNAME, REPO)
    DOWNLOAD_PATH = os.path.join(app.static_folder, "emoji")

    response = requests.get(FULL_URL)

    cached_count = 0
    count = 0
    for image in response.json():
        if not os.path.exists(os.path.abspath(DOWNLOAD_PATH)):
            print("{} does not exist.".format(os.path.abspath(DOWNLOAD_PATH)))
            sys.exit(1)

        full_path = os.path.join(DOWNLOAD_PATH, image["name"])
        if not os.path.exists(full_path):
            count += 1
            f = open(full_path, 'wb')
            f.write(requests.get(image["download_url"]).content)
            f.close()
            if count == cached_count + 50:
                cached_count = count
                print("{} out of {} Emojis downloaded...".format(
                      cached_count, len(response.json())))

    print("Finished downloading {} Emojis.".format(count))

if __name__ == "__main__":
    manager.run()
