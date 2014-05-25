# -*- coding: utf-8 -*-
"""
    flaskbb.utils.populate
    ~~~~~~~~~~~~~~~~~~~~

    A module that makes creating data more easily

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from collections import OrderedDict

from flaskbb.admin.models import Setting
from flaskbb.user.models import User, Group
from flaskbb.forum.models import Post, Topic, Forum, Category

GROUPS = OrderedDict((
    ('Administrator', {
        'description': 'The Administrator Group',
        'admin': True,
        'super_mod': False,
        'mod': False,
        'banned': False,
        'guest': False,
        'editpost': True,
        'deletepost': True,
        'deletetopic': True,
        'posttopic': True,
        'postreply': True,
        'locktopic': True,
        'movetopic': True,
        'mergetopic': True
    }),
    ('Super Moderator', {
        'description': 'The Super Moderator Group',
        'admin': False,
        'super_mod': True,
        'mod': False,
        'banned': False,
        'guest': False,
        'editpost': True,
        'deletepost': True,
        'deletetopic': True,
        'posttopic': True,
        'postreply': True,
        'locktopic': True,
        'movetopic': True,
        'mergetopic': True
    }),
    ('Moderator', {
        'description': 'The Moderator Group',
        'admin': False,
        'super_mod': False,
        'mod': True,
        'banned': False,
        'guest': False,
        'editpost': True,
        'deletepost': True,
        'deletetopic': True,
        'posttopic': True,
        'postreply': True,
        'locktopic': True,
        'movetopic': True,
        'mergetopic': True
    }),
    ('Member', {
        'description': 'The Member Group',
        'admin': False,
        'super_mod': False,
        'mod': False,
        'banned': False,
        'guest': False,
        'editpost': True,
        'deletepost': False,
        'deletetopic': False,
        'posttopic': True,
        'postreply': True,
        'locktopic': False,
        'movetopic': False,
        'mergetopic': False
    }),
    ('Banned', {
        'description': 'The Banned Group',
        'admin': False,
        'super_mod': False,
        'mod': False,
        'banned': True,
        'guest': False,
        'editpost': False,
        'deletepost': False,
        'deletetopic': False,
        'posttopic': False,
        'postreply': False,
        'locktopic': False,
        'movetopic': False,
        'mergetopic': False
    }),
    ('Guest', {
        'description': 'The Guest Group',
        'admin': False,
        'super_mod': False,
        'mod': False,
        'banned': False,
        'guest': True,
        'editpost': False,
        'deletepost': False,
        'deletetopic': False,
        'posttopic': False,
        'postreply': False,
        'locktopic': False,
        'movetopic': False,
        'mergetopic': False
    })
))


DEFAULT_SETTINGS = {
    "project_title": ("FlaskBB", "text"),
    "project_subtitle": ("A lightweight forum software in flask", "text"),
    "default_theme": ("bootstrap3", "text"),
    "tracker_length": (7, "int"),
    "title_length": (15, "int"),
    "online_last_minutes": (15, "int"),
    "users_per_page": (10, "int"),
    "topics_per_page": (10, "int"),
    "posts_per_page": (10, "int")
}


def create_default_settings():
    for key, value in DEFAULT_SETTINGS.items():
            setting = Setting(key=key, value=value[0], value_type=value[1])
            setting.save()


def create_default_groups():
    """
    This will create the 5 default groups
    """
    result = []
    for key, value in GROUPS.items():
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
    user = User(username=username, password=password, email=email,
                date_joined=datetime.utcnow(), primary_group_id=admin_group.id)
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

    create_default_groups()

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
