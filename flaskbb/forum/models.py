# -*- coding: utf-8 -*-
"""
    flaskbb.forum.models
    ~~~~~~~~~~~~~~~~~~~~

    It provides the models for the forum

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from flaskbb.extensions import db
from flaskbb.helpers import DenormalizedText

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id", use_alter=True, name="fk_topic_id", ondelete="CASCADE"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    content = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    date_modified = db.Column(db.DateTime)

    def save(self, user=None, topic=None):
        # update/edit the post
        if self.id:
            db.session.add(self)
            db.session.commit()
            return self

        # Adding a new post
        if user and topic:
            self.user_id = user.id
            self.topic_id = topic.id
            self.date_created = datetime.utcnow()

            # This needs to be done before I update the last_post_id.
            db.session.add(self)
            db.session.commit()

            # Now lets update the last post id
            topic.last_post_id = self.id
            topic.forum.last_post_id = self.id

            # Update the post counts
            user.post_count += 1
            topic.post_count += 1
            topic.forum.post_count += 1

            # And commit it!
            db.session.add(topic)
            db.session.commit()
            return self

    def delete(self):
        # This will delete the whole topic
        if self.topic.first_post_id == self.id:
            self.topic.delete()
            return self

        # Delete the last post
        if self.topic.last_post_id == self.id:
            # Now the second last post will be the last post
            self.topic.last_post_id = self.topic.second_last_post
            self.topic.forum.last_post_id = self.topic.second_last_post
            db.session.commit()

        # Update the post counts
        self.user.post_count -= 1
        self.topic.post_count -= 1
        self.topic.forum.post_count -= 1

        # Is there a better way to do this?
        db.session.delete(self)
        db.session.commit()
        return self


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey("forums.id", use_alter=True, name="fk_forum_id"))
    title = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    locked = db.Column(db.Boolean, default=False)
    important = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    post_count = db.Column(db.Integer, default=0)

    # One-to-one (uselist=False) relationship between first_post and topic
    first_post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE"))
    first_post = db.relationship("Post", backref="first_post", uselist=False, foreign_keys=[first_post_id])

    # One-to-one
    last_post_id = db.Column(db.Integer, db.ForeignKey("posts.id", ondelete="CASCADE", onupdate="CASCADE"))
    last_post = db.relationship("Post", backref="last_post", uselist=False, foreign_keys=[last_post_id])

    # One-to-many
    posts = db.relationship("Post", backref="topic", lazy="joined", primaryjoin="Post.topic_id == Topic.id", cascade="all, delete-orphan", post_update=True)

    def __init__(self, title=None):
        if title:
            self.title = title

    @property
    def second_last_post(self):
        """
        Returns the second last post.
        """
        return self.posts[-2].id

    def save(self, user=None, forum=None, post=None):
        # Updates the topic - Because the thread title (by intention)
        # isn't change able, so we are just going to update the post content
        if self.id:
            db.session.add(self)
            db.session.commit()
            return self

        # Set the forum and user id
        self.forum_id = forum.id
        self.user_id = user.id

        # Update the topic count
        forum.topic_count += 1

        # Insert and commit the topic
        db.session.add(self)
        db.session.commit()

        # Create the topic post
        post.save(user, self)

        # Update the first post id
        self.first_post_id = post.id
        db.session.commit()

        return self

    def delete(self, users=None):
        topic = Topic.query.filter_by(forum_id=self.forum_id).\
            order_by(Topic.last_post_id.desc())

        if topic and topic[0].id == self.id:
            try:
                self.forum.last_post_id = topic[1].last_post_id
            # Catch an IndexError when you delete the last topic in the forum
            except IndexError:
                self.forum.last_post_id = 0

        # These things needs to be stored in a variable before they are deleted
        forum = self.forum

        # Delete the topic
        db.session.delete(self)
        db.session.commit()

        # Update the post counts
        if users:
            # If someone knows a better method for this, feel free to improve it :)
            for user in users:
                user.post_count = Post.query.filter_by(user_id=user.id).count()
                db.session.commit()
        forum.topic_count = Topic.query.filter_by(forum_id=self.forum_id).count()
        forum.post_count = Post.query.filter(Post.topic_id == Topic.id, Topic.forum_id == self.forum_id).count()
        db.session.commit()

        return self


class Forum(db.Model):
    __tablename__ = "forums"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    position = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", use_alter=True, name="fk_category_id"))
    post_count = db.Column(db.Integer, default=0)
    topic_count = db.Column(db.Integer, default=0)

    # One-to-one
    last_post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    last_post = db.relationship("Post", backref="last_post_forum", uselist=False, foreign_keys=[last_post_id])

    # One-to-many
    topics = db.relationship("Topic", backref="forum", lazy="joined")

    moderators = db.Column(DenormalizedText)

    def add_moderator(self, user_id):
        self.moderators.add(user_id)

    def remove_moderator(self, user_id):
        self.moderators.remove(user_id)


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    position = db.Column(db.Integer, default=0)

    # One-to-many
    forums = db.relationship("Forum", backref="category", lazy="joined", primaryjoin="Forum.category_id == Category.id")
