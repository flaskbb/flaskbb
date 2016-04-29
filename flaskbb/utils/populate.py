# -*- coding: utf-8 -*-
"""
    flaskbb.utils.populate
    ~~~~~~~~~~~~~~~~~~~~

    A module that makes creating data more easily

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from flaskbb.management.models import Setting, SettingsGroup
from flaskbb.user.models import User, Group
from flaskbb.forum.models import Post, Topic, Forum, Category


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
    updated_settings = {}

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
            updated_settings[group] = []

        for settings in settingsgroup[1]["settings"]:

            setting = Setting.query.filter_by(key=settings[0]).first()

            if (setting is not None and overwrite_setting) or setting is None:

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


def create_admin_user(username, password, email):
    """Creates the administrator user.
    Returns the created admin user.

    :param username: The username of the user.

    :param password: The password of the user.

    :param email: The email address of the user.
    """

    admin_group = Group.query.filter_by(admin=True).first()
    user = User()

    user.username = username
    user.password = password
    user.email = email
    user.primary_group_id = admin_group.id
    user.activated = True

    user.save()
    return user


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

    # lets send them a few private messages
    for i in range(1, 3):
        # TODO
        pass

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

            for t in range(1, topics + 1):
                # create a topic
                topic = Topic()
                post = Post()

                topic.title = "Test Title %s" % j
                post.content = "Test Content"
                topic.save(post=post, user=user1, forum=forum)
                data_created['topics'] += 1

                for p in range(1, posts + 1):
                    # create a second post in the forum
                    post = Post()
                    post.content = "Test Post"
                    post.save(user=user2, topic=topic)
                    data_created['posts'] += 1

    return data_created


def insert_mass_data(topics=100, posts=100):
    """Creates a few topics in the first forum and each topic has
    a few posts. WARNING: This might take very long!
    Returns the count of created topics and posts.

    :param topics: The amount of topics in the forum.
    :param posts: The number of posts in each topic.
    """
    user1 = User.query.filter_by(id=1).first()
    user2 = User.query.filter_by(id=2).first()
    forum = Forum.query.filter_by(id=1).first()

    created_posts = 0
    created_topics = 0

    if not (user1 or user2 or forum):
        return False

    # create 1000 topics
    for i in range(1, topics + 1):

        # create a topic
        topic = Topic()
        post = Post()

        topic.title = "Test Title %s" % i
        post.content = "Test Content"
        topic.save(post=post, user=user1, forum=forum)
        created_topics += 1

        # create 100 posts in each topic
        for j in range(1, posts + 1):
            post = Post()
            post.content = "Test Post"
            post.save(user=user2, topic=topic)
            created_posts += 1

    return created_topics, created_posts
