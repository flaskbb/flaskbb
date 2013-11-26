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
from flaskbb.utils.types import DenormalizedText
from flaskbb.utils.query import TopicQuery
from helpers import get_forum_ids


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id", use_alter=True,
                                                   name="fk_topic_id",
                                                   ondelete="CASCADE"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    content = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    date_modified = db.Column(db.DateTime)

    # Methods
    def __repr__(self):
        """
        Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.id)

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
            topic.last_updated = datetime.utcnow()
            topic.forum.last_post_id = self.id

            # Update the post counts
            user.post_count += 1
            topic.post_count += 1
            topic.forum.post_count += 1

            # Update the parent forums
            parent = topic.forum.parent
            while parent is not None and not parent.is_category:
                parent.last_post_id = self.id
                parent.post_count += 1
                parent = parent.parent

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

            # check if the last_post is also the last post in the forum
            topic = Topic.query.\
                filter(Topic.forum_id.in_(get_forum_ids(self.topic.forum))).\
                order_by(Topic.last_post_id.desc()).first()

            if self.topic.last_post_id == topic.last_post_id:
                # Update the parent forums
                forum = self.topic.forum
                while forum is not None and not forum.is_category:
                    forum.last_post_id = self.topic.second_last_post
                    forum = forum.parent
                db.session.commit()

        # Update the post counts
        forum = self.topic.forum
        while forum is not None and not forum.is_category:
            forum.post_count -= 1
            forum = forum.parent

        self.user.post_count -= 1
        self.topic.post_count -= 1

        db.session.delete(self)
        db.session.commit()
        return self


class Topic(db.Model):
    __tablename__ = "topics"

    query_class = TopicQuery

    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey("forums.id", use_alter=True,
                                                   name="fk_forum_id"))
    title = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    last_updated = db.Column(db.DateTime, default=datetime.utcnow())
    locked = db.Column(db.Boolean, default=False)
    important = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    post_count = db.Column(db.Integer, default=0)

    # One-to-one (uselist=False) relationship between first_post and topic
    first_post_id = db.Column(db.Integer, db.ForeignKey("posts.id",
                                                        ondelete="CASCADE"))
    first_post = db.relationship("Post", backref="first_post", uselist=False,
                                 foreign_keys=[first_post_id])

    # One-to-one
    last_post_id = db.Column(db.Integer, db.ForeignKey("posts.id",
                                                       ondelete="CASCADE",
                                                       onupdate="CASCADE"))
    last_post = db.relationship("Post", backref="last_post", uselist=False,
                                foreign_keys=[last_post_id])

    # One-to-many
    posts = db.relationship("Post", backref="topic", lazy="joined",
                            primaryjoin="Post.topic_id == Topic.id",
                            cascade="all, delete-orphan", post_update=True)

    # Properties
    @property
    def second_last_post(self):
        """
        Returns the second last post.
        """
        return self.posts[-2].id

    # Methods
    def __init__(self, title=None):
        if title:
            self.title = title

    def __repr__(self):
        """
        Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.id)

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

        # Insert and commit the topic
        db.session.add(self)
        db.session.commit()

        # Create the topic post
        post.save(user, self)

        # Update the first post id
        self.first_post_id = post.id

        # Update the topic count
        forum.topic_count += 1

        # Update the parent forums
        parent = forum.parent
        while parent is not None and not parent.is_category:
            # Update the topic and post count
            parent.topic_count += 1
            parent = parent.parent

        db.session.commit()

        return self

    def delete(self, users=None):
        # Grab the second last topic in the forum + parents/childs
        topic = Topic.query.\
            filter(Topic.forum_id.in_(get_forum_ids(self.forum))).\
            order_by(Topic.last_post_id.desc()).limit(2).offset(0).all()

        # check if the topic is the most recently one in this forum
        try:
            forum = self.forum
            if self.id == topic[0].id:
                # Now the second last post will be the last post
                while forum is not None and not forum.is_category:
                    forum.last_post_id = topic[1].last_post_id
                    forum.save()
                    forum = forum.parent
            else:
                forum.last_post_id = topic[1].last_post_id
        # Catch an IndexError when you delete the last topic in the forum
        except IndexError:
            while forum is not None and not forum.is_category:
                forum.last_post_id = 0
                forum.save()
                forum = forum.parent

        # These things needs to be stored in a variable before they are deleted
        forum = self.forum

        # Delete the topic
        db.session.delete(self)
        db.session.commit()

        # Update the post counts
        if users:
            # If someone knows a better method for this,
            # feel free to improve it :)
            for user in users:
                user.post_count = Post.query.filter_by(user_id=user.id).count()
                db.session.commit()

        while forum is not None and not forum.is_category:
            forum.topic_count = Topic.query.filter_by(
                forum_id=self.forum_id).count()

            forum.post_count = Post.query.filter(
                Post.topic_id == Topic.id,
                Topic.forum_id == self.forum_id).count()

            forum = forum.parent

        db.session.commit()
        return self

    def update_read(self, user, forum=None):
        """
        Update the topics read status if the user hasn't read the latest
        post.
        """
        # Don't do anything if the user is a guest
        if not user.is_authenticated():
            return

        topicread = TopicsRead.query.\
            filter(TopicsRead.user_id == user.id,
                   TopicsRead.topic_id == self.id).first()

        # If the user has visited this topic already but hasn't read
        # it for a while, mark the topic as read
        if topicread and (topicread.last_read < self.last_post.date_created):
            topicread.last_read = datetime.utcnow()
            topicread.save()
        # If the user hasn't read the topic, add him to the topicsread model
        elif not topicread:
            topicread = TopicsRead()
            topicread.user_id = user.id
            topicread.topic_id = self.id
            topicread.last_read = datetime.utcnow()
            topicread.save()

        if forum:
            # fetch the unread posts in the forum
            unread_count = Topic.query.\
                outerjoin(TopicsRead,
                          db.and_(TopicsRead.topic_id == Topic.id,
                                  TopicsRead.user_id == user.id)).\
                outerjoin(ForumsRead,
                          db.and_(ForumsRead.forum_id == Topic.forum_id,
                                  ForumsRead.user_id == user.id)).\
                filter(Topic.forum_id == forum.id,
                       db.or_(TopicsRead.last_read == None,
                              TopicsRead.last_read < Topic.last_updated)).\
                count()
                # Why doesn't this work with when you pass an last_post object?
                # Line 294 e.q.: TopicsRead.last_read < last_post.date_created

            # Mark it as read if no unread topics are found
            if unread_count == 0:
                forumread = ForumsRead.query.\
                    filter(ForumsRead.user_id == user.id,
                           ForumsRead.forum_id == forum.id).first()

                # If the user has never visited a topic in this forum
                # create a new entry
                if not forumread:
                    forumread = ForumsRead(user_id=user.id, forum_id=forum.id)

                forumread.last_read = datetime.utcnow()
                forumread.save()


class Forum(db.Model):
    __tablename__ = "forums"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    position = db.Column(db.Integer, default=0)
    is_category = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("forums.id"))
    locked = db.Column(db.Boolean, default=False)

    post_count = db.Column(db.Integer, default=0)
    topic_count = db.Column(db.Integer, default=0)

    # One-to-one
    last_post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    last_post = db.relationship("Post", backref="last_post_forum",
                                uselist=False, foreign_keys=[last_post_id])

    # One-to-many
    topics = db.relationship("Topic", backref="forum", lazy="joined",
                             cascade="all, delete-orphan")
    children = db.relationship("Forum",
                               backref=db.backref("parent", remote_side=[id]),
                               cascade="all, delete-orphan")

    moderators = db.Column(DenormalizedText)

    # Methods
    def __repr__(self):
        """
        Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.id)

    def add_moderator(self, user_id):
        self.moderators.add(user_id)

    def remove_moderator(self, user_id):
        self.moderators.remove(user_id)

    def get_breadcrumbs(self):
        breadcrumbs = []
        parent = self.parent
        while parent is not None:
            breadcrumbs.append(parent)
            parent = parent.parent

        breadcrumbs.reverse()
        return breadcrumbs

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self, users=None):
        # Delete the forum
        db.session.delete(self)

        # Also delete the child forums
        if self.children:
            for child in self.children:
                db.session.delete(child)

        # Update the parent forums if any
        if self.parent:
            forum = self.parent
            while forum is not None and not forum.is_category:
                forum.topic_count = Topic.query.filter_by(
                    forum_id=forum.id).count()

                forum.post_count = Post.query.filter(
                    Post.topic_id == Topic.id,
                    Topic.forum_id == forum.id).count()

                forum = forum.parent

        db.session.commit()

        # Update the users post count
        if users:
            for user in users:
                user.post_count = Post.query.filter_by(user_id=user.id).count()
                db.session.commit()
        return self


topictracker = db.Table(
    'topictracker',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('topic_id', db.Integer(), db.ForeignKey('topics.id')))


class TopicsRead(db.Model):
    __tablename__ = "topicsread"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"),
                         primary_key=True)
    last_read = db.Column(db.DateTime, default=datetime.utcnow())

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self


class ForumsRead(db.Model):
    __tablename__ = "forumsread"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey("topics.id"),
                         primary_key=True)
    last_read = db.Column(db.DateTime, default=datetime.utcnow())

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
