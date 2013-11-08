# -*- coding: utf-8 -*-
"""
    flaskbb.utils.populate
    ~~~~~~~~~~~~~~~~~~~~

    A module that makes creating data more easily

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from collections import OrderedDict

from flaskbb.extensions import db
from flaskbb.user.models import User, Group
from flaskbb.forum.models import Post, Topic, Forum


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
        'viewtopic': True,
        'viewprofile': True
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
        'viewtopic': True,
        'viewprofiles': True
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
        'viewtopic': True,
        'viewprofile': True
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
        'viewtopic': True,
        'viewprofile': True
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
        'viewtopic': False,
        'viewprofile': False
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
        'viewtopic': False,
        'viewprofile': False
    })
))


def create_default_groups():
    """
    This will create the 5 default groups
    """
    for key, value in GROUPS.items():
        group = Group(name=key)

        for k, v in value.items():
            setattr(group, k, v)

        group.save()


def create_admin_user(username, password, email):
    """
    Creates the administrator user
    """
    admin_group = Group.query.filter_by(admin=True).first()
    user = User(username=username, password=password, email=email)
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

    category = Forum(is_category=True, title="My Category")
    category.save()

    forum = Forum(title="Welcome", description="Your first forum",
                  parent_id=category.id)
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

    # create a category
    category = Forum(is_category=True, title="Test Category",
                     description="Test Description")
    category.save()

    # create 2 forums in the category
    for i in range(1, 3):
        forum_title = "Test Forum %s " % i
        forum = Forum(title=forum_title, description="Test Description",
                      parent_id=1)
        forum.save()

        # Create a subforum
        subforum_title = "Test Subforum %s " % i
        subforum = Forum(title=subforum_title,
                         description="Test Description", parent_id=forum.id)
        subforum.save()

    user = User.query.filter_by(id=1).first()

    # create 1 topic in each forum
    for i in range(2, 6):  # Forum ids are not sequential because categories.
        forum = Forum.query.filter_by(id=i).first()

        topic = Topic()
        post = Post()

        topic.title = "Test Title %s" % (i-1)
        post.content = "Test Content"
        topic.save(user=user, forum=forum, post=post)
