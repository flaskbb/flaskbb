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
        db.session.add(user)
        db.session.commit()

    # create 2 categories
    for i in range(1, 3):
        category_title = "Test Category %s" % i
        category = Forum(is_category=True, title=category_title,
                         description="Test Description")
        db.session.add(category)

        # create 2 forums in each category
        for j in range(1, 3):
            if i == 2:
                j += 2

            forum_title = "Test Forum %s %s" % (j, i)
            forum = Forum(title=forum_title, description="Test Description",
                          parent_id=i)
            db.session.add(forum)
        db.session.commit()

    # create 1 topic in each forum
    for k in [2, 3, 5, 6]:  # Forum ids are not sequential because categories.
        topic = Topic()
        topic.first_post = Post()

        topic.title = "Test Title %s" % k
        topic.user_id = 1
        topic.forum_id = k
        topic.first_post.content = "Test Content"
        topic.first_post.user_id = 1
        topic.first_post.topic_id = topic.id

        db.session.add(topic)
        db.session.commit()

        # Update the post and topic count
        topic.forum.topic_count += 1
        topic.forum.post_count += 1
        topic.post_count += 1
        topic.first_post.user.post_count += 1
        db.session.commit()

    db.session.commit()
