# -*- coding: utf-8 -*-
"""
    flaskbb.utils.populate
    ~~~~~~~~~~~~~~~~~~~~

    A module that makes creating data more easily

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flaskbb.management.models import Setting, SettingsGroup
from flaskbb.user.models import User, Group
from flaskbb.forum.models import Post, Topic, Forum, Category


def delete_settings_from_fixture(fixture):
    """Deletes the settings from a fixture from the database.

    :param fixture: The fixture that should be deleted.
    """
    for settingsgroup in fixture:
        group = SettingsGroup.query.filter_by(key=settingsgroup[0]).first()

        for settings in settingsgroup[1]["settings"]:
            setting = Setting.query.filter_by(key=settings[0]).first()
            setting.delete()
        group.delete()


def create_settings_from_fixture(fixture):
    """Inserts the settings from a fixture into the database.

    :param fixture: The fixture which should inserted.
    """
    for settingsgroup in fixture:
        group = SettingsGroup(
            key=settingsgroup[0],
            name=settingsgroup[1]["name"],
            description=settingsgroup[1]["description"]
        )

        group.save()

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
            setting.save()


def update_settings_from_fixture(fixture, overwrite_group=False,
                                 overwrite_setting=False):
    """Updates the database settings from a fixture.
    Returns the number of updated groups and settings.

    :param fixture: The fixture which should be inserted/updated.

    :param overwrite_group: Set this to ``True`` if you want to overwrite
                            the group if it already exists.
                            Defaults to ``False``.

    :param overwrite_setting: Set this to ``True`` if you want to overwrite the
                              setting if it already exists.
                              Defaults to ``False``.
    """
    groups_count = 0
    settings_count = 0
    for settingsgroup in fixture:

        group = SettingsGroup.query.filter_by(key=settingsgroup[0]).first()

        if (group is not None and overwrite_group) or group is None:
            groups_count += 1

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

            if (setting is not None and overwrite_setting) or setting is None:
                settings_count += 1

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

    return groups_count, settings_count


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

    user.save()


def create_welcome_forum():
    """This will create the `welcome forum` with a welcome topic."""

    if User.query.count() < 1:
        raise "You need to create the admin user first!"

    user = User.query.filter_by(id=1).first()

    category = Category(title="My Category", position=1)
    category.save()

    forum = Forum(title="Welcome", description="Your first forum",
                  category_id=category.id)
    forum.save()

    topic = Topic(title="Welcome!")
    post = Post(content="Have fun with your new FlaskBB Forum!")

    topic.save(user=user, forum=forum, post=post)


def create_test_data():
    """Creates 5 users, 2 categories and 2 forums in each category.
    It also creates a new topic topic in each forum with a post.
    """
    create_default_groups()
    create_default_settings()

    # create 5 users
    for u in range(1, 6):
        username = "test%s" % u
        email = "test%s@example.org" % u
        user = User(username=username, password="test", email=email)
        user.primary_group_id = u
        user.save()

    user1 = User.query.filter_by(id=1).first()
    user2 = User.query.filter_by(id=2).first()

    # create 2 categories
    for i in range(1, 3):
        category_title = "Test Category %s" % i
        category = Category(title=category_title,
                            description="Test Description")
        category.save()

        # create 2 forums in each category
        for j in range(1, 3):
            if i == 2:
                j += 2

            forum_title = "Test Forum %s %s" % (j, i)
            forum = Forum(title=forum_title, description="Test Description",
                          category_id=i)
            forum.save()

            # create a topic
            topic = Topic()
            post = Post()

            topic.title = "Test Title %s" % j
            post.content = "Test Content"
            topic.save(post=post, user=user1, forum=forum)

            # create a second post in the forum
            post = Post()
            post.content = "Test Post"
            post.save(user=user2, topic=topic)


def insert_mass_data(topics=100, posts=100):
    """Creates 100 topics in the first forum and each topic has 100 posts.
    Returns ``True`` if the topics and posts were successfully created.

    :param topics: The amount of topics in the forum.
    :param posts: The number of posts in each topic.
    """
    user1 = User.query.filter_by(id=1).first()
    user2 = User.query.filter_by(id=2).first()
    forum = Forum.query.filter_by(id=1).first()

    if not user1 or user2 or forum:
        raise "Please make sure that there are at least 2 users and 1 forum."

    # create 1000 topics
    for i in range(1, topics+1):

        # create a topic
        topic = Topic()
        post = Post()

        topic.title = "Test Title %s" % i
        post.content = "Test Content"
        topic.save(post=post, user=user1, forum=forum)

        # create 100 posts in each topic
        for j in range(1, posts):
            post = Post()
            post.content = "Test Post"
            post.save(user=user2, topic=topic)
