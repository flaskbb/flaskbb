# -*- coding: utf-8 -*-
"""
    flaskbb.forum.models
    ~~~~~~~~~~~~~~~~~~~~

    It provides the models for the forum

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
from datetime import datetime

from flaskbb.extensions import db, cache
from flaskbb.helpers import DenormalizedText
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
        return "<{} {})>".format(self.__class__.__name__, self.id)

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

            # Invalidate relevant caches
            user.invalidate_cache()
            topic.invalidate_cache()
            topic.forum.invalidate_cache()

            # And commit it!
            db.session.add(topic)
            db.session.commit()
            return self

    def delete(self):
        # This will delete the whole topic
        if self.topic.first_post_id == self.id:
            self.topic.delete()
            return self

        # Invalidate relevant caches
        self.user.invalidate_cache()
        self.topic.invalidate_cache()
        self.topic.forum.invalidate_cache()

        # Is there a better way to do this?
        db.session.delete(self)
        db.session.commit()
        return self


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey("forums.id", use_alter=True,
                                                   name="fk_forum_id"))
    title = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    locked = db.Column(db.Boolean, default=False)
    important = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)

    # One-to-many
    posts = db.relationship("Post", backref="topic", lazy="joined",
                            primaryjoin="Post.topic_id == Topic.id",
                            cascade="all, delete-orphan", post_update=True)

    # Properties
    @property
    def post_count(self):
        """
        Property interface for get_post_count method.

        Method seperate for easy invalidation of cache.
        """
        return self.get_post_count()

    @property
    def first_post(self):
        """
        Property interface for get_first_post method.

        Method seperate for easy invalidation of cache.
        """
        return self.get_first_post()

    @property
    def last_post(self):
        """
        Property interface for get_last_post method.

        Method seperate for easy invalidation of cache.
        """
        return self.get_last_post()

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
        return "<{} {})>".format(self.__class__.__name__, self.id)

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

        # Invalidate relevant caches
        self.invalidate_cache()
        self.forum.invalidate_cache()

        db.session.commit()

        return self

    def delete(self, users=None):
        # Invalidate relevant caches
        self.invalidate_cache()
        self.forum.invalidate_cache()

        # Invalidate user post counts
        if users:
            for user in users:
                user.invalidate_cache()

        # Delete the topic
        db.session.delete(self)
        db.session.commit()

        return self

    @cache.memoize(timeout=sys.maxint)
    def get_post_count(self):
        """
        Returns the amount of posts within the current topic.
        """
        return Post.query.\
            filter(Post.topic_id == self.id).\
            count()

    @cache.memoize(timeout=sys.maxint)
    def get_first_post(self):
        """
        Returns the first post within the current topic.
        """

        post = Post.query.\
            filter(Post.topic_id == self.id).\
            order_by(Post.date_created.asc()).\
            first()

        # Load the topic and user before we cache
        post.topic
        post.user

        return post

    @cache.memoize(timeout=sys.maxint)
    def get_last_post(self):
        """
        Returns the latest post within the current topic.
        """

        post = Post.query.\
            filter(Post.topic_id == self.id).\
            order_by(Post.date_created.desc()).\
            first()

        # Load the topic and user before we cache
        post.topic
        post.user

        return post

    def invalidate_cache(self):
        """
        Invalidates this objects cached metadata.
        """
        cache.delete_memoized(self.get_post_count, self)
        cache.delete_memoized(self.get_first_post, self)
        cache.delete_memoized(self.get_last_post, self)


class Forum(db.Model):
    __tablename__ = "forums"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    position = db.Column(db.Integer, default=0)
    is_category = db.Column(db.Boolean, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("forums.id"))
    locked = db.Column(db.Boolean, default=False)

    # One-to-many
    topics = db.relationship("Topic", backref="forum", lazy="joined")
    children = db.relationship("Forum", backref=db.backref("parent", remote_side=[id]))

    moderators = db.Column(DenormalizedText)  # TODO: No forum_moderators column?

    # Properties
    @property
    def post_count(self):
        """
        Property interface for get_post_count method.

        Method seperate for easy invalidation of cache.
        """
        return self.get_post_count()

    @property
    def topic_count(self):
        """
        Property interface for get_topic_count method.

        Method seperate for easy invalidation of cache.
        """
        return self.get_topic_count()

    @property
    def last_post(self):
        """
        Property interface for get_last_post method.

        Method seperate for easy invalidation of cache.
        """
        return self.get_last_post()

    # Methods
    def __repr__(self):
        """
        Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {})>".format(self.__class__.__name__, self.id)

    def add_moderator(self, user_id):
        self.moderators.add(user_id)

    def remove_moderator(self, user_id):
        self.moderators.remove(user_id)

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    def get_breadcrumbs(self):
        breadcrumbs = []
        parent = self.parent
        while parent is not None:
            breadcrumbs.append(parent)
            parent = parent.parent

        breadcrumbs.reverse()
        return breadcrumbs

    @cache.memoize(timeout=sys.maxint)
    def get_post_count(self, include_children=True):
        """
        Returns the amount of posts within the current forum or it's children.
        Children can be excluded by setting the second parameter to 'false'.
        """

        if include_children:
            return Post.query.\
                filter(Post.topic_id == Topic.id). \
                filter(Topic.forum_id.in_(get_forum_ids(self))). \
                count()
        else:
            return Post.query.\
                filter(Post.topic_id == Topic.id).\
                filter(Topic.forum_id == self.id).\
                count()

    @cache.memoize(timeout=sys.maxint)
    def get_topic_count(self, include_children=True):
        """
        Returns the amount of topics within the current forum or it's children.
        Children can be excluded by setting the second parameter to 'false'.
        """

        if include_children:
            return Topic.query.\
                filter(Topic.forum_id.in_(get_forum_ids(self))). \
                count()
        else:
            return Topic.query.\
                filter(Topic.forum_id == self.id).\
                count()

    @cache.memoize(timeout=sys.maxint)
    def get_last_post(self, include_children=True):
        """
        Returns the latest post within the current forum or it's children.
        Children can be excluded by setting the second parameter to 'false'.
        """

        if include_children:
            post = Post.query.\
                filter(Post.topic_id == Topic.id). \
                filter(Topic.forum_id.in_(get_forum_ids(self))). \
                order_by(Post.date_created.desc()). \
                first()
        else:
            post = Post.query.\
                filter(Post.topic_id == Topic.id).\
                filter(Topic.forum_id == self.id).\
                order_by(Post.date_created.desc()).\
                first()

        # Load the topic and user before we cache
        post.topic
        post.user

        return post

    def invalidate_cache(self):
        """
        Invalidates this objects, and it's parents', cached metadata.
        """
        _forum = self
        while _forum.parent:
            cache.delete_memoized(self.get_post_count, _forum)
            cache.delete_memoized(self.get_topic_count, _forum)
            cache.delete_memoized(self.get_last_post, _forum)
            _forum = _forum.parent

    # Class methods
    @classmethod
    def get_categories(cls):
        return cls.query.filter(cls.is_category)


"""
A topic can be tracked by many users
and a user can track many topics.. so it's a many-to-many relationship
"""
topictracker = db.Table('topictracker',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('topic_id', db.Integer(), db.ForeignKey('topics.id')))


class Tracking(db.Model):
    """
    This model tracks the unread/read posts
    Note: This functionality isn't implemented yet, but this will be the next
    feature after the TopicTracker
    """
    __tablename__ = "tracking"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"))
    last_read = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        """
        Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {})>".format(self.__class__.__name__, self.id)

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
