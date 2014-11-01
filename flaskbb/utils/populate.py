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
    """
    Deletes the settings from a fixture from the database.
    """
    for settingsgroup in fixture:
        group = SettingsGroup.query.filter_by(key=settingsgroup[0]).first()

        for settings in settingsgroup[1]['settings']:
            setting = Setting.query.filter_by(key=settings[0]).first()
            setting.delete()
        group.delete()


def create_settings_from_fixture(fixture):
    """
    Inserts the settings from a fixture into the database.
    """
    for settingsgroup in fixture:
        group = SettingsGroup(
            key=settingsgroup[0],
            name=settingsgroup[1]['name'],
            description=settingsgroup[1]['description']
        )

        group.save()

        for settings in settingsgroup[1]['settings']:
            setting = Setting(
                key=settings[0],
                value=settings[1]['value'],
                value_type=settings[1]['value_type'],
                name=settings[1]['name'],
                description=settings[1]['description'],
                extra=settings[1].get('extra', ""),     # Optional field

                settingsgroup=group.key
            )
            setting.save()


def create_default_settings():
    """
    Creates the default settings
    """
    from flaskbb.fixtures.settings import fixture
    create_settings_from_fixture(fixture)


def create_default_groups():
    """
    This will create the 5 default groups
    """
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
    """
    Creates the administrator user
    """
    admin_group = Group.query.filter_by(admin=True).first()
    user = User()

    user.username = username
    user.password = password
    user.email = email
    user.primary_group_id = admin_group.id

    user.save()


def create_welcome_forum():
    """
    This will create the `welcome forum` that nearly every
    forum software has after the installation process is finished
    """

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
    """
    Creates 5 users, 2 categories and 2 forums in each category. It also opens
    a new topic topic in each forum with a post.
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
