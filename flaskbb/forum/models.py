# -*- coding: utf-8 -*-
"""
    flaskbb.forum.models
    ~~~~~~~~~~~~~~~~~~~~

    It provides the models for the forum

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta

from flask import current_app

from flaskbb.extensions import db
from flaskbb.utils.types import SetType, MutableSet
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
        """Saves a new post. If no parameters are passed we assume that
        you will just update an existing post. It returns the object after the
        operation was successful.

        :param user: The user who has created the post

        :param topic: The topic in which the post was created
        """
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
            # TODO: Improvement - store the parent forums in a list and then
            # get all the forums with one query instead of firing up
            # for each parent a own query
            while parent is not None and not parent.is_category:
                parent.last_post_id = self.id
                parent.post_count += 1
                parent = parent.parent

            # And commit it!
            db.session.add(topic)
            db.session.commit()
            return self

    def delete(self):
        """Deletes a post and returns self"""
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
    last_post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))

    last_post = db.relationship("Post", backref="last_post", uselist=False,
                                foreign_keys=[last_post_id])

    # One-to-many
    posts = db.relationship("Post", backref="topic", lazy="joined",
                            primaryjoin="Post.topic_id == Topic.id",
                            cascade="all, delete-orphan", post_update=True)

    # Properties
    @property
    def second_last_post(self):
        """Returns the second last post."""
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
        """Saves a topic and returns the topic object. If no parameters are
        given, it will only update the topic.

        :param user: The user who has created the topic

        :param forum: The forum where the topic is stored

        :param post: The post object which is connected to the topic
        """
        # Updates the topic
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
        """Deletes a topic with the corresponding posts. If a list with
        user objects is passed it will also update their post counts

        :param users: A list with user objects
        """
        # Grab the second last topic in the forum + parents/childs
        topic = Topic.query.\
            filter(Topic.forum_id.in_(get_forum_ids(self.forum))).\
            order_by(Topic.last_post_id.desc()).limit(2).offset(0).all()

        # check if the topic is the most recently one in this forum
        try:
            forum = self.forum
            # you want to delete the topic with the last post
            if self.id == topic[0].id:
                # Now the second last post will be the last post
                while forum is not None and not forum.is_category:
                    forum.last_post_id = topic[1].last_post_id
                    forum.save()
                    forum = forum.parent
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
            forum.topic_count -= 1
            forum.post_count -= 1

            forum = forum.parent

        db.session.commit()
        return self

    def update_read(self, user, forum, forumsread=None):
        """Update the topics read status if the user hasn't read the latest
        post.

        :param user: The user for whom the readstracker should be updated

        :param forum: The forum in which the topic is

        :param forumsread: The forumsread object. It is used to check if there
                           is a new post since the forum has been marked as
                           read
        """

        read_cutoff = datetime.utcnow() - timedelta(
            days=current_app.config['TRACKER_LENGTH'])

        # Anonymous User or the post is too old for inserting it in the
        # TopicsRead model
        if not user.is_authenticated() or \
                read_cutoff > self.last_post.date_created:
            return

        topicread = TopicsRead.query.\
            filter(TopicsRead.user_id == user.id,
                   TopicsRead.topic_id == self.id).first()

        # Can be None if the user has never marked the forum as read. If this
        # condition is false - we need to update the tracker
        if forumsread and forumsread.cleared is not None and \
                forumsread.cleared >= self.last_post.date_created:
            return

        # A new post has been submitted that the user hasn't read.
        # Updating...
        if topicread and (topicread.last_read < self.last_post.date_created):
            topicread.last_read = datetime.utcnow()
            topicread.save()

        # The user has not visited the topic before. Inserting him in
        # the TopicsRead model.
        elif not topicread:
            topicread = TopicsRead()
            topicread.user_id = user.id
            topicread.topic_id = self.id
            topicread.forum_id = self.forum_id
            topicread.last_read = datetime.utcnow()
            topicread.save()

        # else: no unread posts

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

            #No unread topics available - trying to mark the forum as read
            if unread_count == 0:
                forumread = ForumsRead.query.\
                    filter(ForumsRead.user_id == user.id,
                           ForumsRead.forum_id == forum.id).first()

                # ForumsRead is already up-to-date.
                if forumread and forumread.last_read > topicread.last_read:
                    return

                # ForumRead Entry exists - Updating it because a new post
                # has been submitted that the user hasn't read.
                elif forumread:
                    forumread.last_read = datetime.utcnow()
                    forumread.save()

                # No ForumRead Entry existing - creating one.
                else:
                    forumread = ForumsRead()
                    forumread.user_id = user.id
                    forumread.forum_id = forum.id
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

    moderators = db.Column(MutableSet.as_mutable(SetType))

    # A set with all parent forums
    parents = db.Column(MutableSet.as_mutable(SetType))

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
        """Saves a forum"""
        db.session.add(self)
        db.session.commit()

        parent_ids = []
        parent = self.parent
        while parent and not parent.is_category:
            parent_ids.append(parent.id)
            parent = parent.parent

        for parent_id in parent_ids:
            self.parents.add(parent_id)

        db.session.add(self)
        db.session.commit()
        return self

    def delete(self, users=None):
        """Deletes forum. If a list with involved user objects is passed,
        it will also update their post counts

        :param users: A list with user objects
        """
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
    forum_id = db.Column(db.Integer, db.ForeignKey("forums.id"),
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
    cleared = db.Column(db.DateTime)

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
