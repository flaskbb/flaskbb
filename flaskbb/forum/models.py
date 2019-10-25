# -*- coding: utf-8 -*-
"""
    flaskbb.forum.models
    ~~~~~~~~~~~~~~~~~~~~

    It provides the models for the forum

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
from datetime import timedelta

from flask import abort, current_app, url_for
from sqlalchemy.orm import aliased

from flaskbb.extensions import db
from flaskbb.utils.database import (CRUDMixin, HideableCRUDMixin, UTCDateTime,
                                    make_comparable)
from flaskbb.utils.helpers import (get_categories_and_forums, get_forums,
                                   slugify, time_utcnow, topic_is_unread)
from flaskbb.utils.settings import flaskbb_config

logger = logging.getLogger(__name__)


moderators = db.Table(
    'moderators',
    db.Column('user_id', db.Integer(),
              db.ForeignKey('users.id', ondelete="CASCADE"),
              nullable=False),
    db.Column('forum_id', db.Integer(),
              db.ForeignKey('forums.id', ondelete="CASCADE"),
              nullable=False))


topictracker = db.Table(
    'topictracker',
    db.Column('user_id', db.Integer(),
              db.ForeignKey('users.id', ondelete="CASCADE"),
              nullable=False),
    db.Column('topic_id', db.Integer(),
              db.ForeignKey('topics.id', ondelete="CASCADE"),
              nullable=False))


forumgroups = db.Table(
    'forumgroups',
    db.Column('group_id', db.Integer(),
              db.ForeignKey('groups.id', ondelete="CASCADE"),
              nullable=False),
    db.Column('forum_id', db.Integer(),
              db.ForeignKey('forums.id', ondelete="CASCADE"),
              nullable=False))


class TopicsRead(db.Model, CRUDMixin):
    __tablename__ = "topicsread"

    user_id = db.Column(db.Integer,
                        db.ForeignKey("users.id", ondelete="CASCADE"),
                        primary_key=True)
    user = db.relationship('User', uselist=False, foreign_keys=[user_id])
    topic_id = db.Column(db.Integer,
                         db.ForeignKey("topics.id", ondelete="CASCADE"),
                         primary_key=True)
    topic = db.relationship('Topic', uselist=False, foreign_keys=[topic_id])
    forum_id = db.Column(db.Integer,
                         db.ForeignKey("forums.id", ondelete="CASCADE"),
                         primary_key=True)
    forum = db.relationship('Forum', uselist=False, foreign_keys=[forum_id])
    last_read = db.Column(UTCDateTime(timezone=True), default=time_utcnow,
                          nullable=False)


class ForumsRead(db.Model, CRUDMixin):
    __tablename__ = "forumsread"

    user_id = db.Column(db.Integer,
                        db.ForeignKey("users.id", ondelete="CASCADE"),
                        primary_key=True)
    user = db.relationship('User', uselist=False, foreign_keys=[user_id])
    forum_id = db.Column(db.Integer,
                         db.ForeignKey("forums.id", ondelete="CASCADE"),
                         primary_key=True)
    forum = db.relationship('Forum', uselist=False, foreign_keys=[forum_id])
    last_read = db.Column(UTCDateTime(timezone=True), default=time_utcnow,
                          nullable=False)
    cleared = db.Column(UTCDateTime(timezone=True), nullable=True)


@make_comparable
class Report(db.Model, CRUDMixin):
    __tablename__ = "reports"

    # TODO: Store in addition to the info below topic title and username
    # as well. So that in case a user or post gets deleted, we can
    # still view the report

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                            nullable=True)
    reported = db.Column(UTCDateTime(timezone=True), default=time_utcnow,
                         nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=True)
    zapped = db.Column(UTCDateTime(timezone=True), nullable=True)
    zapped_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reason = db.Column(db.Text, nullable=True)

    post = db.relationship(
        "Post", lazy="joined",
        backref=db.backref('report', cascade='all, delete-orphan')
    )
    reporter = db.relationship("User", lazy="joined",
                               foreign_keys=[reporter_id])
    zapper = db.relationship("User", lazy="joined", foreign_keys=[zapped_by])

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.id)

    def save(self, post=None, user=None):
        """Saves a report.

        :param post: The post that should be reported
        :param user: The user who has reported the post
        :param reason: The reason why the user has reported the post
        """

        if self.id:
            db.session.add(self)
            db.session.commit()
            return self

        if post and user:
            self.reporter = user
            self.reported = time_utcnow()
            self.post = post

        db.session.add(self)
        db.session.commit()
        return self


@make_comparable
class Post(HideableCRUDMixin, db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer,
                         db.ForeignKey("topics.id", ondelete="CASCADE",
                                       use_alter=True),
                         nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(UTCDateTime(timezone=True), default=time_utcnow,
                             nullable=False)
    date_modified = db.Column(UTCDateTime(timezone=True), nullable=True)
    modified_by = db.Column(db.String(200), nullable=True)

    # Properties
    @property
    def url(self):
        """Returns the url for the post."""
        return url_for("forum.view_post", post_id=self.id)

    # Methods
    def __init__(self, content=None, user=None, topic=None):
        """Creates a post object with some initial values.

        :param content: The content of the post.
        :param user: The user of the post.
        :param topic: Can either be the topic_id or the topic object.
        """
        if content:
            self.content = content

        if user:
            # setting user here -- even with setting the user id explicitly
            # breaks the bulk insert for some reason
            self.user_id = user.id
            self.username = user.username

        if topic:
            self.topic_id = topic if isinstance(topic, int) else topic.id

        self.date_created = time_utcnow()

    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.id)

    def is_first_post(self):
        """Checks whether this post is the first post in the topic or not."""
        return self.topic.is_first_post(self)

    def save(self, user=None, topic=None):
        """Saves a new post. If no parameters are passed we assume that
        you will just update an existing post. It returns the object after the
        operation was successful.

        :param user: The user who has created the post
        :param topic: The topic in which the post was created
        """
        current_app.pluggy.hook.flaskbb_event_post_save_before(post=self)

        # update/edit the post
        if self.id:
            db.session.add(self)
            db.session.commit()
            current_app.pluggy.hook.flaskbb_event_post_save_after(post=self,
                                                                  is_new=False)
            return self

        # Adding a new post
        if user and topic:
            created = time_utcnow()
            self.user = user
            self.username = user.username
            self.topic = topic
            self.date_created = created

            if not topic.hidden:
                topic.last_updated = created
                topic.last_post = self

                # Update the last post info for the forum
                topic.forum.last_post = self
                topic.forum.last_post_user = self.user
                topic.forum.last_post_title = topic.title
                topic.forum.last_post_username = user.username
                topic.forum.last_post_created = created

                # Update the post counts
                user.post_count += 1
                topic.post_count += 1
                topic.forum.post_count += 1

            # And commit it!
            db.session.add(topic)
            db.session.commit()
            current_app.pluggy.hook.flaskbb_event_post_save_after(post=self,
                                                                  is_new=True)
            return self

    def delete(self):
        """Deletes a post and returns self."""
        # This will delete the whole topic
        if self.topic.first_post == self:
            self.topic.delete()
            return self

        db.session.delete(self)

        self._deal_with_last_post()
        self._update_counts()

        db.session.commit()
        return self

    def hide(self, user):
        if self.hidden:
            return

        if self.topic.first_post == self:
            self.topic.hide(user)
            return self

        super(Post, self).hide(user)
        self._deal_with_last_post()
        self._update_counts()
        db.session.commit()
        return self

    def unhide(self):
        if not self.hidden:
            return

        if self.topic.first_post == self:
            self.topic.unhide()
            return self

        self._restore_post_to_topic()
        super(Post, self).unhide()
        self._update_counts()
        db.session.commit()
        return self

    def _deal_with_last_post(self):
        if self.topic.last_post == self:

            # update the last post in the forum
            if self.topic.last_post == self.topic.forum.last_post:
                # We need the second last post in the forum here,
                # because the last post will be deleted
                second_last_post = Post.query.filter(
                    Post.topic_id == Topic.id,
                    Topic.forum_id == self.topic.forum.id,
                    Post.hidden != True,
                    Post.id != self.id
                ).order_by(
                    Post.id.desc()
                ).limit(1).first()

                if second_last_post:
                    # now lets update the second last post to the last post
                    self.topic.forum.last_post = second_last_post
                    self.topic.forum.last_post_title = second_last_post.topic.title  # noqa
                    self.topic.forum.last_post_user = second_last_post.user
                    self.topic.forum.last_post_username = second_last_post.username  # noqa
                    self.topic.forum.last_post_created = second_last_post.date_created  # noqa
                else:
                    self.topic.forum.last_post = None
                    self.topic.forum.last_post_title = None
                    self.topic.forum.last_post_user = None
                    self.topic.forum.last_post_username = None
                    self.topic.forum.last_post_created = None

            # check if there is a second last post in this topic
            if self.topic.second_last_post is not None:
                # Now the second last post will be the last post
                self.topic.last_post_id = self.topic.second_last_post

            # there is no second last post, now the last post is also the
            # first post
            else:
                self.topic.last_post = self.topic.first_post

            self.topic.last_updated = self.topic.last_post.date_created

    def _update_counts(self):
        if self.hidden:
            clauses = [Post.hidden != True, Post.id != self.id]
        else:
            clauses = [db.or_(Post.hidden != True, Post.id == self.id)]

        user_post_clauses = clauses + [
            Post.user_id == self.user.id,
            Topic.id == Post.topic_id,
            Topic.hidden != True,
        ]

        # Update the post counts
        self.user.post_count = Post.query.filter(*user_post_clauses).count()

        if self.topic.hidden:
            self.topic.post_count = 0
        else:
            topic_post_clauses = clauses + [
                Post.topic_id == self.topic.id,
            ]
            self.topic.post_count = Post.query.filter(
                *topic_post_clauses
            ).count()

        forum_post_clauses = clauses + [
            Post.topic_id == Topic.id,
            Topic.forum_id == self.topic.forum.id,
            Topic.hidden != True,
        ]

        self.topic.forum.post_count = Post.query.filter(
            *forum_post_clauses
        ).count()

    def _restore_post_to_topic(self):
        last_unhidden_post = Post.query.filter(
            Post.topic_id == self.topic_id,
            Post.id != self.id,
            Post.hidden != True,
        ).limit(1).first()

        # should never be None, but deal with it anyways to be safe
        if (
            last_unhidden_post and
            self.date_created > last_unhidden_post.date_created
        ):
            self.topic.last_post = self
            self.second_last_post = last_unhidden_post

            # if we're the newest in the topic again, we might be the newest
            # in the forum again only set if our parent topic isn't hidden
            if (
                not self.topic.hidden and
                (
                    not self.topic.forum.last_post or
                    self.date_created > self.topic.forum.last_post.date_created
                )
            ):
                self.topic.forum.last_post = self
                self.topic.forum.last_post_title = self.topic.title
                self.topic.forum.last_post_user = self.user
                self.topic.forum.last_post_username = self.username
                self.topic.forum.last_post_created = self.date_created


@make_comparable
class Topic(HideableCRUDMixin, db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer,
                         db.ForeignKey("forums.id", ondelete="CASCADE"),
                         nullable=False)
    title = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username = db.Column(db.String(200), nullable=False)
    date_created = db.Column(UTCDateTime(timezone=True), default=time_utcnow,
                             nullable=False)
    last_updated = db.Column(UTCDateTime(timezone=True), default=time_utcnow,
                             nullable=False)
    locked = db.Column(db.Boolean, default=False, nullable=False)
    important = db.Column(db.Boolean, default=False, nullable=False)
    views = db.Column(db.Integer, default=0, nullable=False)
    post_count = db.Column(db.Integer, default=0, nullable=False)

    # One-to-one (uselist=False) relationship between first_post and topic
    first_post_id = db.Column(db.Integer,
                              db.ForeignKey("posts.id", ondelete="CASCADE"),
                              nullable=True)
    first_post = db.relationship("Post", backref="first_post", uselist=False,
                                 foreign_keys=[first_post_id])

    # One-to-one
    last_post_id = db.Column(db.Integer, db.ForeignKey("posts.id"),
                             nullable=True)

    last_post = db.relationship("Post", backref="last_post", uselist=False,
                                foreign_keys=[last_post_id])

    # One-to-many
    posts = db.relationship("Post", backref="topic", lazy="dynamic",
                            primaryjoin="Post.topic_id == Topic.id",
                            cascade="all, delete-orphan",
                            post_update=True)

    @property
    def second_last_post(self):
        """Returns the second last post or None."""
        try:
            return self.posts[-2].id
        except IndexError:
            return None

    @property
    def slug(self):
        """Returns a slugified version of the topic title."""
        return slugify(self.title)

    @property
    def url(self):
        """Returns the slugified url for the topic."""
        return url_for("forum.view_topic", topic_id=self.id, slug=self.slug)

    def __init__(self, title=None, user=None, content=None):
        """Creates a topic object with some initial values.

        :param title: The title of the topic.
        :param user: The user of the post.
        """
        if title:
            self.title = title

        if user:
            # setting the user here, even with setting the id, breaks the bulk
            # insert stuff as they use the session.bulk_save_objects which does
            # not trigger relationships
            self.user_id = user.id
            self.username = user.username

        if content:
            self._post = Post(content=content)

        self.date_created = self.last_updated = time_utcnow()

    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.id)

    def is_first_post(self, post):
        """Checks if the post is the first post in the topic.

        :param post: The post object.
        """
        return self.first_post_id == post.id

    def first_unread(self, topicsread, user, forumsread=None):
        """Returns the url to the first unread post. If no unread posts exist
        it will return the url to the topic.

        :param topicsread: The topicsread object for the topic
        :param user: The user who should be checked if he has read the
                     last post in the topic
        :param forumsread: The forumsread object in which the topic is. If you
                        also want to check if the user has marked the forum as
                        read, than you will also need to pass an forumsread
                        object.
        """
        # If the topic is unread try to get the first unread post
        if topic_is_unread(self, topicsread, user, forumsread):
            query = Post.query.filter(Post.topic_id == self.id)
            if topicsread is not None:
                query = query.filter(Post.date_created > topicsread.last_read)
            post = query.order_by(Post.id.asc()).first()
            if post is not None:
                return post.url

        return self.url

    @classmethod
    def get_topic(cls, topic_id, user):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        return topic

    def tracker_needs_update(self, forumsread, topicsread):
        """Returns True if the topicsread tracker needs an update.
        Also, if the ``TRACKER_LENGTH`` is configured, it will just recognize
        topics that are newer than the ``TRACKER_LENGTH`` (in days) as unread.

        :param forumsread: The ForumsRead object is needed because we also
                           need to check if the forum has been cleared
                           sometime ago.
        :param topicsread: The topicsread object is used to check if there is
                           a new post in the topic.
        """
        read_cutoff = None
        if flaskbb_config['TRACKER_LENGTH'] > 0:
            read_cutoff = time_utcnow() - timedelta(
                days=flaskbb_config['TRACKER_LENGTH'])

        # The tracker is disabled - abort
        if read_cutoff is None:
            logger.debug("Readtracker is disabled.")
            return False

        # Else the topic is still below the read_cutoff
        elif read_cutoff > self.last_post.date_created:
            logger.debug("Topic is below the read_cutoff (too old).")
            return False

        # Can be None (cleared) if the user has never marked the forum as read.
        # If this condition is false - we need to update the tracker
        if forumsread and forumsread.cleared is not None and \
                forumsread.cleared >= self.last_post.date_created:
            logger.debug("User has marked the forum as read. No new posts "
                         "since then.")
            return False

        if topicsread and topicsread.last_read >= self.last_post.date_created:
            logger.debug("The last post in this topic has already been read.")
            return False

        logger.debug("Topic is unread.")
        return True

    def update_read(self, user, forum, forumsread):
        """Updates the topicsread and forumsread tracker for a specified user,
        if the topic contains new posts or the user hasn't read the topic.
        Returns True if the tracker has been updated.

        :param user: The user for whom the readstracker should be updated.
        :param forum: The forum in which the topic is.
        :param forumsread: The forumsread object. It is used to check if there
                           is a new post since the forum has been marked as
                           read.
        """
        # User is not logged in - abort
        if not user.is_authenticated:
            return False

        topicsread = TopicsRead.query.\
            filter(TopicsRead.user_id == user.id,
                   TopicsRead.topic_id == self.id).first()

        if not self.tracker_needs_update(forumsread, topicsread):
            return False

        # Because we return True/False if the trackers have been
        # updated, we need to store the status in a temporary variable
        updated = False

        # A new post has been submitted that the user hasn't read.
        # Updating...
        if topicsread:
            logger.debug("Updating existing TopicsRead '{}' object."
                         .format(topicsread))
            topicsread.last_read = time_utcnow()
            topicsread.save()
            updated = True

        # The user has not visited the topic before. Inserting him in
        # the TopicsRead model.
        elif not topicsread:
            logger.debug("Creating new TopicsRead object.")
            topicsread = TopicsRead()
            topicsread.user = user
            topicsread.topic = self
            topicsread.forum = self.forum
            topicsread.last_read = time_utcnow()
            topicsread.save()
            updated = True

        # No unread posts
        else:
            updated = False

        # Save True/False if the forums tracker has been updated.
        updated = forum.update_read(user, forumsread, topicsread)

        return updated

    def recalculate(self):
        """Recalculates the post count in the topic."""
        post_count = Post.query.filter_by(topic_id=self.id).count()
        self.post_count = post_count
        self.save()
        return self

    def move(self, new_forum):
        """Moves a topic to the given forum.
        Returns True if it could successfully move the topic to forum.

        :param new_forum: The new forum for the topic
        """

        # if the target forum is the current forum, abort
        if self.forum == new_forum:
            return False

        old_forum = self.forum
        self.forum.post_count -= self.post_count
        self.forum.topic_count -= 1
        self.forum = new_forum

        new_forum.post_count += self.post_count
        new_forum.topic_count += 1

        db.session.commit()

        new_forum.update_last_post()
        old_forum.update_last_post()

        TopicsRead.query.filter_by(topic_id=self.id).delete()

        return True

    def save(self, user=None, forum=None, post=None):
        """Saves a topic and returns the topic object. If no parameters are
        given, it will only update the topic.

        :param user: The user who has created the topic
        :param forum: The forum where the topic is stored
        :param post: The post object which is connected to the topic
        """
        current_app.pluggy.hook.flaskbb_event_topic_save_before(topic=self)

        # Updates the topic
        if self.id:
            db.session.add(self)
            db.session.commit()
            current_app.pluggy.hook.flaskbb_event_topic_save_after(
                topic=self, is_new=False
            )
            return self

        # Set the forum and user id
        self.forum = forum
        self.user = user
        self.username = user.username

        # Set the last_updated time. Needed for the readstracker
        self.date_created = self.last_updated = time_utcnow()

        # Insert and commit the topic
        db.session.add(self)
        db.session.commit()

        if post is not None:
            self._post = post

        # Create the topic post
        self._post.save(user, self)

        # Update the first and last post id
        self.last_post = self.first_post = self._post

        # Update the topic count
        forum.topic_count += 1
        db.session.commit()

        current_app.pluggy.hook.flaskbb_event_topic_save_after(topic=self,
                                                               is_new=True)
        return self

    def delete(self):
        """Deletes a topic with the corresponding posts."""

        forum = self.forum
        # get the users before deleting the topic
        invovled_users = self.involved_users().all()

        db.session.delete(self)
        self._fix_user_post_counts(invovled_users)
        self._fix_post_counts(forum)

        # forum.last_post_id shouldn't usually be none
        if forum.last_post_id is None or \
                self.last_post_id == forum.last_post_id:
            forum.update_last_post(commit=False)

        db.session.commit()
        return self

    def hide(self, user):
        """Soft deletes a topic from a forum

        :param user: The user who hid the topic.
        """
        if self.hidden:
            return

        involved_users = self.involved_users().all()
        self._remove_topic_from_forum()
        super(Topic, self).hide(user)
        self._handle_first_post()
        self._fix_user_post_counts(involved_users)
        self._fix_post_counts(self.forum)
        db.session.commit()
        return self

    def unhide(self):
        """Restores a hidden topic to a forum"""
        if not self.hidden:
            return

        involved_users = self.involved_users().all()
        super(Topic, self).unhide()
        self._handle_first_post()
        self._restore_topic_to_forum()
        self._fix_user_post_counts(involved_users)
        self.forum.recalculate()
        db.session.commit()
        return self

    def _remove_topic_from_forum(self):
        # Grab the second last topic in the forum + parents/childs
        topics = Topic.query.filter(
            Topic.forum_id == self.forum_id,
            Topic.hidden != True
        ).order_by(
            Topic.last_post_id.desc()
        ).limit(2).offset(0).all()

        # do we want to replace the topic with the last post in the forum?
        if len(topics) > 1:
            if topics[0] == self:
                # Now the second last post will be the last post
                self.forum.last_post = topics[1].last_post
                self.forum.last_post_title = topics[1].title
                self.forum.last_post_user = topics[1].user
                self.forum.last_post_username = topics[1].username
                self.forum.last_post_created = topics[1].last_updated
        else:
            self.forum.last_post = None
            self.forum.last_post_title = None
            self.forum.last_post_user = None
            self.forum.last_post_username = None
            self.forum.last_post_created = None

    def _fix_user_post_counts(self, users=None):
        # Update the post counts
        if users:
            for user in users:
                user.post_count = Post.query.filter(
                    Post.user_id == user.id,
                    Topic.id == Post.topic_id,
                    Topic.hidden != True,
                    Post.hidden != True
                ).count()

    def _fix_post_counts(self, forum):
        clauses = [
            Topic.forum_id == forum.id
        ]
        if self.hidden:
            clauses.extend([
                Topic.id != self.id,
                Topic.hidden != True,
            ])
        else:
            clauses.append(db.or_(Topic.id == self.id, Topic.hidden != True))

        forum.topic_count = Topic.query.filter(*clauses).count()

        post_count = clauses + [
            Post.topic_id == Topic.id,
        ]

        if self.hidden:
            post_count.append(Post.hidden != True)
        else:
            post_count.append(
                db.or_(Post.hidden != True, Post.id == self.first_post.id)
            )

        forum.post_count = Post.query.distinct().filter(*post_count).count()

    def _restore_topic_to_forum(self):
        if (
            self.forum.last_post is None or
            self.forum.last_post_created < self.last_updated
        ):
            self.forum.last_post = self.last_post
            self.forum.last_post_title = self.title
            self.forum.last_post_user = self.user
            self.forum.last_post_username = self.username
            self.forum.last_post_created = self.last_updated

    def _handle_first_post(self):
        # have to do this specially because otherwise we start recurisve calls
        self.first_post.hidden = self.hidden
        self.first_post.hidden_by = self.hidden_by
        self.first_post.hidden_at = self.hidden_at

    def involved_users(self):
        """
        Returns a query of all users involved in the topic
        """
        # todo: Find circular import and break it
        from flaskbb.user.models import User
        return User.query.distinct().filter(
            Post.topic_id == self.id, User.id == Post.user_id
        )


@make_comparable
class Forum(db.Model, CRUDMixin):
    __tablename__ = "forums"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer,
                            db.ForeignKey("categories.id", ondelete="CASCADE"),
                            nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, default=1, nullable=False)
    locked = db.Column(db.Boolean, default=False, nullable=False)
    show_moderators = db.Column(db.Boolean, default=False, nullable=False)
    external = db.Column(db.String(200), nullable=True)

    post_count = db.Column(db.Integer, default=0, nullable=False)
    topic_count = db.Column(db.Integer, default=0, nullable=False)

    # One-to-one
    last_post_id = db.Column(db.Integer, db.ForeignKey("posts.id"),
                             nullable=True)  # we handle this case ourselfs
    last_post = db.relationship("Post", backref="last_post_forum",
                                uselist=False, foreign_keys=[last_post_id])

    # set to null if the user got deleted
    last_post_user_id = db.Column(db.Integer,
                                  db.ForeignKey("users.id",
                                                ondelete="SET NULL"),
                                  nullable=True)

    last_post_user = db.relationship("User", uselist=False,
                                     foreign_keys=[last_post_user_id])

    # Not nice, but needed to improve the performance; can be set to NULL
    # if the forum has no posts
    last_post_title = db.Column(db.String(255), nullable=True)
    last_post_username = db.Column(db.String(255), nullable=True)
    last_post_created = db.Column(UTCDateTime(timezone=True),
                                  default=time_utcnow, nullable=True)

    # One-to-many
    topics = db.relationship("Topic", backref="forum", lazy="dynamic",
                             cascade="all, delete-orphan")

    # Many-to-many
    moderators = db.relationship(
        "User",
        secondary=moderators,
        primaryjoin=(moderators.c.forum_id == id),
        backref=db.backref("forummoderator", lazy="dynamic"),
        lazy="joined"
    )
    groups = db.relationship(
        "Group",
        secondary=forumgroups,
        primaryjoin=(forumgroups.c.forum_id == id),
        backref="forumgroups",
        lazy="joined",
    )

    # Properties
    @property
    def slug(self):
        """Returns a slugified version from the forum title"""
        return slugify(self.title)

    @property
    def url(self):
        """Returns the slugified url for the forum"""
        if self.external:
            return self.external
        return url_for("forum.view_forum", forum_id=self.id, slug=self.slug)

    @property
    def last_post_url(self):
        """Returns the url for the last post in the forum"""
        return url_for("forum.view_post", post_id=self.last_post_id)

    # Methods
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.id)

    def update_last_post(self, commit=True):
        """Updates the last post in the forum."""
        last_post = Post.query.\
            filter(Post.topic_id == Topic.id,
                   Topic.forum_id == self.id).\
            order_by(Post.date_created.desc()).\
            limit(1)\
            .first()

        # Last post is none when there are no topics in the forum
        if last_post is not None:

            # a new last post was found in the forum
            if last_post != self.last_post:
                self.last_post = last_post
                self.last_post_title = last_post.topic.title
                self.last_post_user_id = last_post.user_id
                self.last_post_username = last_post.username
                self.last_post_created = last_post.date_created

        # No post found..
        else:
            self.last_post = None
            self.last_post_title = None
            self.last_post_user = None
            self.last_post_username = None
            self.last_post_created = None

        if commit:
            db.session.commit()

    def update_read(self, user, forumsread, topicsread):
        """Updates the ForumsRead status for the user. In order to work
        correctly, be sure that `topicsread is **not** `None`.

        :param user: The user for whom we should check if he has read the
                     forum.

        :param forumsread: The forumsread object. It is needed to check if
                           if the forum is unread. If `forumsread` is `None`
                           and the forum is unread, it will create a new entry
                           in the `ForumsRead` relation, else (and the forum
                           is still unread) we are just going to update the
                           entry in the `ForumsRead` relation.

        :param topicsread: The topicsread object is used in combination
                           with the forumsread object to check if the
                           forumsread relation should be updated and
                           therefore is unread.
        """
        if not user.is_authenticated or topicsread is None:
            return False

        read_cutoff = None
        if flaskbb_config['TRACKER_LENGTH'] > 0:
            read_cutoff = time_utcnow() - timedelta(
                days=flaskbb_config['TRACKER_LENGTH'])

        # fetch the unread posts in the forum
        unread_count = Topic.query.\
            outerjoin(TopicsRead,
                      db.and_(TopicsRead.topic_id == Topic.id,
                              TopicsRead.user_id == user.id)).\
            outerjoin(ForumsRead,
                      db.and_(ForumsRead.forum_id == Topic.forum_id,
                              ForumsRead.user_id == user.id)).\
            filter(Topic.forum_id == self.id,
                   Topic.last_updated > read_cutoff,
                   db.or_(TopicsRead.last_read == None,  # noqa: E711
                          TopicsRead.last_read < Topic.last_updated),
                   db.or_(ForumsRead.last_read == None,  # noqa: E711
                          ForumsRead.last_read < Topic.last_updated)).\
            count()

        # No unread topics available - trying to mark the forum as read
        if unread_count == 0:
            logger.debug("No unread topics. Trying to mark the forum as read.")

            if forumsread and forumsread.last_read > topicsread.last_read:
                logger.debug("forumsread.last_read is newer than "
                             "topicsread.last_read. Everything is read.")
                return False

            # ForumRead Entry exists - Updating it because a new topic/post
            # has been submitted and has read everything (obviously, else the
            # unread_count would be useless).
            elif forumsread:
                logger.debug("Updating existing ForumsRead '{}' object."
                             .format(forumsread))
                forumsread.last_read = time_utcnow()
                forumsread.save()
                return True

            # No ForumRead Entry existing - creating one.
            logger.debug("Creating new ForumsRead object.")
            forumsread = ForumsRead()
            forumsread.user = user
            forumsread.forum = self
            forumsread.last_read = time_utcnow()
            forumsread.save()
            return True

        # Nothing updated, because there are still more than 0 unread
        # topicsread
        logger.debug("No ForumsRead object updated - there are still {} "
                     "unread topics.".format(unread_count))
        return False

    def recalculate(self, last_post=False):
        """Recalculates the post_count and topic_count in the forum.
        Returns the forum with the recounted stats.

        :param last_post: If set to ``True`` it will also try to update
                          the last post columns in the forum.
        """
        topic_count = Topic.query.filter(
            Topic.forum_id == self.id, Topic.hidden != True
        ).count()
        post_count = Post.query.filter(
            Post.topic_id == Topic.id,
            Topic.forum_id == self.id,
            Post.hidden != True,
            Topic.hidden != True
        ).count()
        self.topic_count = topic_count
        self.post_count = post_count

        if last_post:
            self.update_last_post()

        self.save()
        return self

    def save(self, groups=None):
        """Saves a forum

        :param moderators: If given, it will update the moderators in this
                           forum with the given iterable of user objects.
        :param groups: A list with group objects.
        """
        if self.id:
            db.session.merge(self)
        else:
            if groups is None:
                # importing here because of circular dependencies
                from flaskbb.user.models import Group
                self.groups = Group.query.order_by(Group.name.asc()).all()
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
        db.session.commit()

        # Update the users post count
        if users:
            users_list = []
            for user in users:
                user.post_count = Post.query.filter_by(user_id=user.id).count()
                users_list.append(user)
            db.session.add_all(users_list)
            db.session.commit()

        return self

    def move_topics_to(self, topics):
        """Moves a bunch a topics to the forum. Returns ``True`` if all
        topics were moved successfully to the forum.

        :param topics: A iterable with topic objects.
        """
        status = False
        for topic in topics:
            status = topic.move(self)
        return status

    # Classmethods
    @classmethod
    def get_forum(cls, forum_id, user):
        """Returns the forum and forumsread object as a tuple for the user.

        :param forum_id: The forum id
        :param user: The user object is needed to check if we also need their
                     forumsread object.
        """
        if user.is_authenticated:
            forum, forumsread = Forum.query.\
                filter(Forum.id == forum_id).\
                options(db.joinedload("category")).\
                outerjoin(ForumsRead,
                          db.and_(ForumsRead.forum_id == Forum.id,
                                  ForumsRead.user_id == user.id)).\
                add_entity(ForumsRead).\
                first_or_404()
        else:
            forum = Forum.query.filter(Forum.id == forum_id).first_or_404()
            forumsread = None

        return forum, forumsread

    @classmethod
    def get_topics(cls, forum_id, user, page=1, per_page=20):
        """Get the topics for the forum. If the user is logged in,
        it will perform an outerjoin for the topics with the topicsread and
        forumsread relation to check if it is read or unread.

        :param forum_id: The forum id
        :param user: The user object
        :param page: The page whom should be loaded
        :param per_page: How many topics per page should be shown
        """
        if user.is_authenticated:
            # Now thats intersting - if i don't do the add_entity(Post)
            # the n+1 still exists when trying to access 'topic.last_post'
            # but without it it will fire another query.
            # This way I don't have to use the last_post object when I
            # iterate over the result set.
            topics = Topic.query.filter_by(forum_id=forum_id).\
                outerjoin(TopicsRead,
                          db.and_(TopicsRead.topic_id == Topic.id,
                                  TopicsRead.user_id == user.id)).\
                outerjoin(Post, Topic.last_post_id == Post.id).\
                add_entity(Post).\
                add_entity(TopicsRead).\
                order_by(Topic.important.desc(), Topic.last_updated.desc()).\
                paginate(page, per_page, True)
        else:
            topics = Topic.query.filter_by(forum_id=forum_id).\
                outerjoin(Post, Topic.last_post_id == Post.id).\
                add_entity(Post).\
                order_by(Topic.important.desc(), Topic.last_updated.desc()).\
                paginate(page, per_page, True)

            topics.items = [(topic, last_post, None)
                            for topic, last_post, in topics.items]

        return topics


@make_comparable
class Category(db.Model, CRUDMixin):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, default=1, nullable=False)

    # One-to-many
    forums = db.relationship("Forum", backref="category", lazy="dynamic",
                             primaryjoin='Forum.category_id == Category.id',
                             order_by='asc(Forum.position)',
                             cascade="all, delete-orphan")

    # Properties
    @property
    def slug(self):
        """Returns a slugified version from the category title"""
        return slugify(self.title)

    @property
    def url(self):
        """Returns the slugified url for the category"""
        return url_for("forum.view_category", category_id=self.id,
                       slug=self.slug)

    # Methods
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.id)

    def delete(self, users=None):
        """Deletes a category. If a list with involved user objects is passed,
        it will also update their post counts

        :param users: A list with user objects
        """

        # and finally delete the category itself
        db.session.delete(self)
        db.session.commit()

        # Update the users post count
        if users:
            for user in users:
                user.post_count = Post.query.filter_by(user_id=user.id).count()
                db.session.commit()

        return self

    # Classmethods
    @classmethod
    def get_all(cls, user):
        """Get all categories with all associated forums.
        It returns a list with tuples. Those tuples are containing the category
        and their associated forums (whose are stored in a list).

        For example::

            [(<Category 1>, [(<Forum 2>, <ForumsRead>), (<Forum 1>, None)]),
             (<Category 2>, [(<Forum 3>, None), (<Forum 4>, None)])]

        :param user: The user object is needed to check if we also need their
                     forumsread object.
        """
        # import Group model locally to avoid cicular imports
        from flaskbb.user.models import Group
        if user.is_authenticated:
            # get list of user group ids
            user_groups = [gr.id for gr in user.groups]
            # filter forums by user groups
            user_forums = Forum.query.\
                filter(Forum.groups.any(Group.id.in_(user_groups))).\
                subquery()

            forum_alias = aliased(Forum, user_forums)
            # get all
            forums = cls.query.\
                join(forum_alias, cls.id == forum_alias.category_id).\
                outerjoin(ForumsRead,
                          db.and_(ForumsRead.forum_id == forum_alias.id,
                                  ForumsRead.user_id == user.id)).\
                add_entity(forum_alias).\
                add_entity(ForumsRead).\
                order_by(Category.position, Category.id,
                         forum_alias.position).\
                all()
        else:
            guest_group = Group.get_guest_group()
            # filter forums by guest groups
            guest_forums = Forum.query.\
                filter(Forum.groups.any(Group.id == guest_group.id)).\
                subquery()

            forum_alias = aliased(Forum, guest_forums)
            forums = cls.query.\
                join(forum_alias, cls.id == forum_alias.category_id).\
                add_entity(forum_alias).\
                order_by(Category.position, Category.id,
                         forum_alias.position).\
                all()

        return get_categories_and_forums(forums, user)

    @classmethod
    def get_forums(cls, category_id, user):
        """Get the forums for the category.
        It returns a tuple with the category and the forums with their
        forumsread object are stored in a list.

        A return value can look like this for a category with two forums::

            (<Category 1>, [(<Forum 1>, None), (<Forum 2>, None)])

        :param category_id: The category id
        :param user: The user object is needed to check if we also need their
                     forumsread object.
        """
        from flaskbb.user.models import Group
        if user.is_authenticated:
            # get list of user group ids
            user_groups = [gr.id for gr in user.groups]
            # filter forums by user groups
            user_forums = Forum.query.\
                filter(Forum.groups.any(Group.id.in_(user_groups))).\
                subquery()

            forum_alias = aliased(Forum, user_forums)
            forums = cls.query.\
                filter(cls.id == category_id).\
                join(forum_alias, cls.id == forum_alias.category_id).\
                outerjoin(ForumsRead,
                          db.and_(ForumsRead.forum_id == forum_alias.id,
                                  ForumsRead.user_id == user.id)).\
                add_entity(forum_alias).\
                add_entity(ForumsRead).\
                order_by(forum_alias.position).\
                all()
        else:
            guest_group = Group.get_guest_group()
            # filter forums by guest groups
            guest_forums = Forum.query.\
                filter(Forum.groups.any(Group.id == guest_group.id)).\
                subquery()

            forum_alias = aliased(Forum, guest_forums)
            forums = cls.query.\
                filter(cls.id == category_id).\
                join(forum_alias, cls.id == forum_alias.category_id).\
                add_entity(forum_alias).\
                order_by(forum_alias.position).\
                all()

        if not forums:
            abort(404)

        return get_forums(forums, user)
