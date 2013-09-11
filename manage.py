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

from flask import current_app
from flask.ext.script import Manager, Shell, Server

from flaskbb import create_app
from flaskbb.configs.development import DevelopmentConfig, BaseConfig
from flaskbb.extensions import db

from flaskbb.user.models import User
from flaskbb.forum.models import Post, Topic, Forum, Category

app = create_app(DevelopmentConfig)
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
    dbfile = os.path.join(BaseConfig._basedir, "flaskbb.sqlite")
    if os.path.exists(dbfile):
        print "Removing old database file..."
        os.remove(dbfile)

    db.create_all()

    # create 5 users
    for u in range(1, 6):
        username = "test%s" % u
        email = "test%s@example.org" % u
        user = User(username=username, password="test", email=email)
        db.session.add(user)

    # create 2 categories
    for i in range(1, 3):
        category_title = "Test Category %s" % i
        category = Category(title=category_title, description="Test Description")
        db.session.add(category)

        # create 2 forums in each category
        for j in range(1, 3):
            if i == 2:
                j += 2

            forum_title = "Test Forum %s %s" % (j, i)
            forum = Forum(title=forum_title, description="Test Description",
                          category_id=i)
            db.session.add(forum)

    # create 1 topic in each forum
    for k in range(1, 5):
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

        # Update the post and topic count
        topic.forum.topic_count += 1
        topic.forum.post_count += 1
        topic.post_count += 1
        topic.first_post.user.post_count += 1

        # create 2 additional posts for each topic
        for m in range(1, 3):
            post = Post(content="Test Post", user_id=2, topic_id=k)

            db.session.add(post)
            db.session.commit()

            # Update the post count
            post.user.post_count += 1
            topic.post_count += 1
            topic.forum.post_count += 1

            topic.last_post_id = post.id
            topic.forum.last_post_id = post.id

            db.session.commit()

    db.session.commit()


if __name__ == "__main__":
    manager.run()
