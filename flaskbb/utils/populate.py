# -*- coding: utf-8 -*-
"""
    flaskbb.utils.populate
    ~~~~~~~~~~~~~~~~~~~~~~

    A module that makes creating data more easily

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import unicode_literals

import collections
import logging
import os

from flask import current_app
from sqlalchemy_utils.functions import create_database, database_exists
from alembic.util.exc import CommandError

from flaskbb.extensions import alembic, db
from flaskbb.forum.models import Category, Forum, Post, Topic
from flaskbb.management.models import Setting, SettingsGroup
from flaskbb.user.models import Group, User


logger = logging.getLogger(__name__)


def delete_settings_from_fixture(fixture):
    """Deletes the settings from a fixture from the database.
    Returns the deleted groups and settings.

    :param fixture: The fixture that should be deleted.
    """
    deleted_settings = {}

    for settingsgroup in fixture:
        group = SettingsGroup.query.filter_by(key=settingsgroup[0]).first()
        deleted_settings[group] = []

        for settings in settingsgroup[1]["settings"]:
            setting = Setting.query.filter_by(key=settings[0]).first()
            if setting:
                deleted_settings[group].append(setting)
                setting.delete()

        group.delete()

    return deleted_settings


def create_settings_from_fixture(fixture):
    """Inserts the settings from a fixture into the database.
    Returns the created groups and settings.

    :param fixture: The fixture which should inserted.
    """
    created_settings = {}
    for settingsgroup in fixture:
        group = SettingsGroup(
            key=settingsgroup[0],
            name=settingsgroup[1]["name"],
            description=settingsgroup[1]["description"]
        )
        group.save()
        created_settings[group] = []

        for settings in settingsgroup[1]["settings"]:
            setting = Setting(
                key=settings[0],
                value=settings[1]["value"],
                value_type=settings[1]["value_type"],
                name=settings[1]["name"],
                description=settings[1]["description"],
                extra=settings[1].get("extra", ""),     # Optional field

                settingsgroup=group.key
            )
            if setting:
                setting.save()
                created_settings[group].append(setting)

    return created_settings


def update_settings_from_fixture(fixture, overwrite_group=False,
                                 overwrite_setting=False):
    """Updates the database settings from a fixture.
    Returns the updated groups and settings.

    :param fixture: The fixture which should be inserted/updated.
    :param overwrite_group: Set this to ``True`` if you want to overwrite
                            the group if it already exists.
                            Defaults to ``False``.
    :param overwrite_setting: Set this to ``True`` if you want to overwrite the
                              setting if it already exists.
                              Defaults to ``False``.
    """
    updated_settings = collections.defaultdict(list)

    for settingsgroup in fixture:

        group = SettingsGroup.query.filter_by(key=settingsgroup[0]).first()

        if (group is not None and overwrite_group) or group is None:

            if group is not None:
                group.name = settingsgroup[1]["name"]
                group.description = settingsgroup[1]["description"]
            else:
                group = SettingsGroup(
                    key=settingsgroup[0],
                    name=settingsgroup[1]["name"],
                    description=settingsgroup[1]["description"]
                )

            group.save()

        for settings in settingsgroup[1]["settings"]:

            setting = Setting.query.filter_by(key=settings[0]).first()

            if setting is not None:
                setting_is_different = (
                    setting.value != settings[1]["value"]
                    or setting.value_type != settings[1]["value_type"]
                    or setting.name != settings[1]["name"]
                    or setting.description != settings[1]["description"]
                    or setting.extra != settings[1].get("extra", "")
                    or setting.settingsgroup != group.key
                )

            if (
                setting is not None and
                overwrite_setting and
                setting_is_different
            ) or setting is None:
                if setting is not None:
                    setting.value = settings[1]["value"]
                    setting.value_type = settings[1]["value_type"]
                    setting.name = settings[1]["name"]
                    setting.description = settings[1]["description"]
                    setting.extra = settings[1].get("extra", "")
                    setting.settingsgroup = group.key
                else:
                    setting = Setting(
                        key=settings[0],
                        value=settings[1]["value"],
                        value_type=settings[1]["value_type"],
                        name=settings[1]["name"],
                        description=settings[1]["description"],
                        extra=settings[1].get("extra", ""),
                        settingsgroup=group.key
                    )

                setting.save()
                updated_settings[group].append(setting)
    return updated_settings


def create_default_settings():
    """Creates the default settings."""
    from flaskbb.fixtures.settings import fixture
    create_settings_from_fixture(fixture)


def create_default_groups():
    """This will create the 5 default groups."""
    from flaskbb.fixtures.groups import fixture
    result = []
    for key, value in fixture.items():
        group = Group(name=key)

        for k, v in value.items():
            setattr(group, k, v)

        group.save()
        result.append(group)
    return result


def create_user(username, password, email, groupname):
    """Creates a user.
    Returns the created user.

    :param username: The username of the user.
    :param password: The password of the user.
    :param email: The email address of the user.
    :param groupname: The name of the group to which the user
                      should belong to.
    """
    if groupname == "member":
        group = Group.get_member_group()
    else:
        group = Group.query.filter(getattr(Group, groupname) == True).first()

    user = User.create(username=username, password=password, email=email,
                       primary_group_id=group.id, activated=True)
    return user


def update_user(username, password, email, groupname):
    """Update an existing user.
    Returns the updated user.

    :param username: The username of the user.
    :param password: The password of the user.
    :param email: The email address of the user.
    :param groupname: The name of the group to which the user
                      should belong to.
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        return None

    if groupname == "member":
        group = Group.get_member_group()
    else:
        group = Group.query.filter(getattr(Group, groupname) == True).first()

    user.password = password
    user.email = email
    user.primary_group = group
    return user.save()


def create_welcome_forum():
    """This will create the `welcome forum` with a welcome topic.
    Returns True if it's created successfully.
    """
    if User.query.count() < 1:
        return False

    user = User.query.filter_by(id=1).first()

    category = Category(title="My Category", position=1)
    category.save()

    forum = Forum(title="Welcome", description="Your first forum",
                  category_id=category.id)
    forum.save()

    topic = Topic(title="Welcome!")
    post = Post(content="Have fun with your new FlaskBB Forum!")

    topic.save(user=user, forum=forum, post=post)
    return True


def create_test_data(users=5, categories=2, forums=2, topics=1, posts=1):
    """Creates 5 users, 2 categories and 2 forums in each category.
    It also creates a new topic topic in each forum with a post.
    Returns the amount of created users, categories, forums, topics and posts
    as a dict.

    :param users: The number of users.
    :param categories: The number of categories.
    :param forums: The number of forums which are created in each category.
    :param topics: The number of topics which are created in each forum.
    :param posts: The number of posts which are created in each topic.
    """
    create_default_groups()
    create_default_settings()

    data_created = {'users': 0, 'categories': 0, 'forums': 0,
                    'topics': 0, 'posts': 0}

    # create 5 users
    for u in range(1, users + 1):
        username = "test%s" % u
        email = "test%s@example.org" % u
        user = User(username=username, password="test", email=email)
        user.primary_group_id = u
        user.activated = True
        user.save()
        data_created['users'] += 1

    user1 = User.query.filter_by(id=1).first()
    user2 = User.query.filter_by(id=2).first()

    # create 2 categories
    for i in range(1, categories + 1):
        category_title = "Test Category %s" % i
        category = Category(title=category_title,
                            description="Test Description")
        category.save()
        data_created['categories'] += 1

        # create 2 forums in each category
        for j in range(1, forums + 1):
            if i == 2:
                j += 2

            forum_title = "Test Forum %s %s" % (j, i)
            forum = Forum(title=forum_title, description="Test Description",
                          category_id=i)
            forum.save()
            data_created['forums'] += 1

            for _ in range(1, topics + 1):
                # create a topic
                topic = Topic(title="Test Title %s" % j)
                post = Post(content="Test Content")

                topic.save(post=post, user=user1, forum=forum)
                data_created['topics'] += 1

                for _ in range(1, posts + 1):
                    # create a second post in the forum
                    post = Post(content="Test Post")
                    post.save(user=user2, topic=topic)
                    data_created['posts'] += 1

    return data_created


def insert_bulk_data(topic_count=10, post_count=100):
    """Creates a specified number of topics in the first forum with
    each topic containing a specified amount of posts.
    Returns the number of created topics and posts.

    :param topics: The amount of topics in the forum.
    :param posts: The number of posts in each topic.
    """
    user1 = User.query.filter_by(id=1).first()
    user2 = User.query.filter_by(id=2).first()
    forum = Forum.query.filter_by(id=1).first()

    last_post = Post.query.order_by(Post.id.desc()).first()
    last_post_id = 1 if last_post is None else last_post.id

    created_posts = 0
    created_topics = 0
    posts = []

    if not (user1 or user2 or forum):
        return False

    db.session.begin(subtransactions=True)

    for i in range(1, topic_count + 1):
        last_post_id += 1

        # create a topic
        topic = Topic(title="Test Title %s" % i)
        post = Post(content="First Post")
        topic.save(post=post, user=user1, forum=forum)
        created_topics += 1

        # create some posts in the topic
        for _ in range(1, post_count + 1):
            last_post_id += 1
            post = Post(content="Some other Post", user=user2, topic=topic.id)
            topic.last_updated = post.date_created
            topic.post_count += 1

            # FIXME: Is there a way to ignore IntegrityErrors?
            # At the moment, the first_post_id is also the last_post_id.
            # This does no harm, except that in the forums view, you see
            # the information for the first post instead of the last one.
            # I run a little benchmark:
            # 5.3643078804 seconds to create 100 topics and 10000 posts
            # Using another method (where data integrity is ok) I benchmarked
            # these stats:
            # 49.7832770348 seconds to create 100 topics and 10000 posts

            # Uncomment the line underneath and the other line to reduce
            # performance but fixes the above mentioned problem.
            # topic.last_post_id = last_post_id

            created_posts += 1
            posts.append(post)

        # uncomment this and delete the one below, also uncomment the
        # topic.last_post_id line above. This will greatly reduce the
        # performance.
        # db.session.bulk_save_objects(posts)
    db.session.bulk_save_objects(posts)

    # and finally, lets update some stats
    forum.recalculate(last_post=True)
    user1.recalculate()
    user2.recalculate()

    return created_topics, created_posts


def create_latest_db(target="default@head"):
    """Creates the database including the schema using SQLAlchemy's
    db.create_all method instead of going through all the database revisions.
    The revision will be set to 'head' which indicates the latest alembic
    revision.

    :param target: The target branch. Defaults to 'default@head'.
    """
    if not database_exists(db.engine.url):
        create_database(db.engine.url)

    db.create_all()
    alembic.stamp(target=target)


def run_plugin_migrations(plugins=None):
    """Runs the migrations for a list of plugins.

    :param plugins: A iterable of plugins to run the migrations for. If set
                    to ``None``, all external plugin migrations will be run.
    """
    if plugins is None:
        plugins = current_app.pluggy.get_external_plugins()

    for plugin in plugins:
        plugin_name = current_app.pluggy.get_name(plugin)
        if not os.path.exists(os.path.join(plugin.__path__[0], "migrations")):
            logger.debug("No migrations found for plugin %s" % plugin_name)
            continue
        try:
            alembic.upgrade(target="{}@head".format(plugin_name))
        except CommandError as exc:
            logger.debug("Couldn't run migrations for plugin {} because of "
                         "following exception: ".format(plugin_name),
                         exc_info=exc)
