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
from collections import OrderedDict

from flask import current_app
from flask.ext.script import Manager, Shell, Server

from flaskbb import create_app
from flaskbb.extensions import db

from flaskbb.user.models import User, Group
from flaskbb.forum.models import Post, Topic, Forum

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

    groups = OrderedDict((
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

    # create 5 groups
    for key, value in groups.items():
        group = Group(name=key)

        for k, v in value.items():
            setattr(group, k, v)

        db.session.add(group)
        db.session.commit()

    # create 5 users
    groups = Group.query.all()
    for u in range(1, 6):
        username = "test%s" % u
        email = "test%s@example.org" % u
        user = User(username=username, password="test", email=email)
        user.secondary_groups.append(groups[u-1])
        user.primary_group_id = u
        db.session.add(user)

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

    # create 1 topic in each forum
    for k in [2, 3, 5, 6]:  # Forum ids are not sequential because categories.
        topic = Topic()
        topic.first_post = Post()

        topic.title = "Test Title %s" % k
        topic.user_id = 1
        topic.forum_id = k
        topic.first_post.content = "Test Content"
        topic.first_post.user_id = 1
        topic.first_post.topic_id = k

        db.session.add(topic)
        db.session.commit()

        # Invalidate relevant caches
        topic.invalidate_cache()
        topic.forum.invalidate_cache()

        # create 2 additional posts for each topic
        for m in range(1, 3):
            post = Post(content="Test Post", user_id=2, topic_id=k)

            db.session.add(post)
            db.session.commit()

            # Update the post count
            post.user.invalidate_cache()
            topic.invalidate_cache()
            topic.forum.invalidate_cache()

            db.session.commit()

    db.session.commit()


if __name__ == "__main__":
    manager.run()
