# -*- coding: utf-8 -*-
"""
    flaskbb.forum.models
    ~~~~~~~~~~~~~~~~~~~~

    It provides the models for the forum

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta

from flask import current_app, url_for

from flaskbb.extensions import db
from flaskbb.utils.query import TopicQuery
from flaskbb.utils.helpers import slugify


moderators = db.Table(
    'moderators',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id'),
              nullable=False),
    db.Column('forum_id', db.Integer(),
              db.ForeignKey('forums.id', use_alter=True, name="fk_forum_id"),
              nullable=False))


topictracker = db.Table(
    'topictracker',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id'),
              nullable=False),
    db.Column('topic_id', db.Integer(),
              db.ForeignKey('topics.id',
                            use_alter=True, name="fk_tracker_topic_id"),
              nullable=False))


class TopicsRead(db.Model):
    __tablename__ = "topicsread"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                        primary_key=True)
    topic_id = db.Column(db.Integer,
                         db.ForeignKey("topics.id", use_alter=True,
                                       name="fk_tr_topic_id"),
                         primary_key=True)
    forum_id = db.Column(db.Integer,
                         db.ForeignKey("forums.id", use_alter=True,
                                       name="fk_tr_forum_id"),
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
    forum_id = db.Column(db.Integer,
                         db.ForeignKey("topics.id", use_alter=True,
                                       name="fk_fr_forum_id"),
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


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                            nullable=False)
    reported = db.Column(db.DateTime, default=datetime.utcnow())
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    zapped = db.Column(db.DateTime)
    zapped_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    reason = db.Column(db.String(63))

    post = db.relationship("Post", backref="report", lazy="joined")
    reporter = db.relationship("User", lazy="joined",
                               foreign_keys=[reporter_id])
    zapper = db.relationship("User", lazy="joined", foreign_keys=[zapped_by])

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
            self.reporter_id = user.id
            self.reported = datetime.utcnow()
            self.post_id = post.id

        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self


class Post(db.Model):
    __tablename__ = "posts"
    __searchable__ = ['content', 'username']

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer,
                         db.ForeignKey("topics.id",
                                       use_alter=True,
                                       name="fk_post_topic_id",
                                       ondelete="CASCADE"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    username = db.Column(db.String(15), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    date_modified = db.Column(db.DateTime)
    modified_by = db.Column(db.String(15))

    # Properties
    @property
    def url(self):
        """Returns the url for the post"""
        return url_for("forum.view_post", post_id=self.id)

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
            self.username = user.username
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
        """Deletes a post and returns self"""
        # This will delete the whole topic
        if self.topic.first_post_id == self.id:
            self.topic.delete()
            return self

        # Delete the last post
        if self.topic.last_post_id == self.id:

            # update the last post in the forum
            if self.topic.last_post_id == self.topic.forum.last_post_id:
                # We need the second last post in the forum here,
                # because the last post will be deleted
                second_last_post = Post.query.\
                    filter(Post.topic_id == Topic.id,
                           Topic.forum_id == self.topic.forum.id).\
                    order_by(Post.id.desc()).limit(2).offset(0).\
                    all()

                second_last_post = second_last_post[1]

                self.topic.forum.last_post_id = second_last_post.id

            # check if there is a second last post, else it is the first post
            if self.topic.second_last_post:
                # Now the second last post will be the last post
                self.topic.last_post_id = self.topic.second_last_post

            # there is no second last post, now the last post is also the
            # first post
            else:
                self.topic.last_post_id = self.topic.first_post_id

        # Update the post counts
        self.user.post_count -= 1
        self.topic.post_count -= 1
        self.topic.forum.post_count -= 1
        db.session.commit()

        db.session.delete(self)
        db.session.commit()
        return self


class Topic(db.Model):
    __tablename__ = "topics"
    __searchable__ = ['title', 'username']

    query_class = TopicQuery

    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer,
                         db.ForeignKey("forums.id",
                                       use_alter=True,
                                       name="fk_topic_forum_id"),
                         nullable=False)
    title = db.Column(db.String(63), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    username = db.Column(db.String(15), nullable=False)
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

    @property
    def slug(self):
        """Returns a slugified version from the topic title"""
        return slugify(self.title)

    @property
    def url(self):
        """Returns the url for the topic"""
        return url_for("forum.view_topic", topic_id=self.id, slug=self.slug)

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

    def move(self, forum):
        """Moves a topic to the given forum.
        Returns True if it could successfully move the topic to forum.

        :param forum: The new forum for the topic
        """

        # if the target forum is the current forum, abort
        if self.forum_id == forum.id:
            return False

        old_forum = self.forum
        self.forum.post_count -= self.post_count
        self.forum.topic_count -= 1
        self.forum_id = forum.id

        forum.post_count += self.post_count
        forum.topic_count += 1

        db.session.commit()

        forum.update_last_post()
        old_forum.update_last_post()

        TopicsRead.query.filter_by(topic_id=self.id).delete()

        return True

    def merge(self, topic):
        """Merges a topic with another topic

        :param topic: The new topic for the posts in this topic
        """

        # You can only merge a topic with a differrent topic in the same forum
        if self.id == topic.id or not self.forum_id == topic.forum_id:
            return False

        # Update the topic id
        Post.query.filter_by(topic_id=self.id).\
            update({Post.topic_id: topic.id})

        # Update the last post
        if topic.last_post.date_created < self.last_post.date_created:
            topic.last_post_id = self.last_post_id

        # Increase the post and views count
        topic.post_count += self.post_count
        topic.views += self.views

        topic.save()

        # Finally delete the old topic
        Topic.query.filter_by(id=self.id).delete()

        return True

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
        self.username = user.username

        # Insert and commit the topic
        db.session.add(self)
        db.session.commit()

        # Create the topic post
        post.save(user, self)

        # Update the first post id
        self.first_post_id = post.id

        # Update the topic count
        forum.topic_count += 1
        db.session.commit()

        return self

    def delete(self, users=None):
        """Deletes a topic with the corresponding posts. If a list with
        user objects is passed it will also update their post counts

        :param users: A list with user objects
        """
        # Grab the second last topic in the forum + parents/childs
        topic = Topic.query.\
            filter_by(forum_id=self.forum_id).\
            order_by(Topic.last_post_id.desc()).limit(2).offset(0).all()

        # do want to delete the topic with the last post?
        if topic and topic[0].id == self.id:
            try:
                # Now the second last post will be the last post
                self.forum.last_post_id = topic[1].last_post_id
            # Catch an IndexError when you delete the last topic in the forum
            # There is no second last post
            except IndexError:
                self.forum.last_post_id = 0

        # These things needs to be stored in a variable before they are deleted
        forum = self.forum

        # Delete the topic
        db.session.delete(self)
        db.session.commit()

        # Update the post counts
        if users:
            for user in users:
                user.post_count = Post.query.filter_by(user_id=user.id).count()
                db.session.commit()

        forum.topic_count = Topic.query.\
            filter_by(forum_id=self.forum_id).\
            count()

        forum.post_count = Post.query.\
            filter(Post.topic_id == Topic.id,
                   Topic.forum_id == self.forum_id).\
            count()

        TopicsRead.query.filter_by(topic_id=self.id).delete()

        db.session.commit()
        return self

    def tracker_needs_update(self, forumsread, topicsread):
        """Returns True if the tracker needs an update.
        TODO: Couldn't think of a better name for this method - ideas?

        :param forumsread: The ForumsRead object is needed because we also
                           need to check if the forum has been cleared
                           sometime ago.

        :param topicsread: The topicsread object is used to check if there is
                           a new post in the topic.
        """
        read_cutoff = None
        if current_app.config['TRACKER_LENGTH'] > 0:
            read_cutoff = datetime.utcnow() - timedelta(
                days=current_app.config['TRACKER_LENGTH'])

        # The tracker is disabled - abort
        if read_cutoff is None:
            return False

        # Else the topic is still below the read_cutoff
        elif read_cutoff > self.last_post.date_created:
            return False

        # Can be None (cleared) if the user has never marked the forum as read.
        # If this condition is false - we need to update the tracker
        if forumsread and forumsread.cleared is not None and \
                forumsread.cleared >= self.last_post.date_created:
            return False

        if topicsread and topicsread.last_read >= self.last_post.date_created:
            return False

        return True

    def update_read(self, user, forum, forumsread):
        """Updates the topicsread and forumsread tracker for a specified user,
        if the topic contains new posts or the user hasn't read the topic.
        Also, if the ``TRACKER_LENGTH`` is configured, it will just recognize
        topics that are newer than the ``TRACKER_LENGTH`` (days) as unread.
        Returns True if the tracker has been updated.

        :param user: The user for whom the readstracker should be updated.

        :param forum: The forum in which the topic is.

        :param forumsread: The forumsread object. It is used to check if there
                           is a new post since the forum has been marked as
                           read.
        """
        # User is not logged in - abort
        if not user.is_authenticated():
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
            topicsread.last_read = datetime.utcnow()
            topicsread.save()
            updated = True

        # The user has not visited the topic before. Inserting him in
        # the TopicsRead model.
        elif not topicsread:
            topicsread = TopicsRead()
            topicsread.user_id = user.id
            topicsread.topic_id = self.id
            topicsread.forum_id = self.forum_id
            topicsread.last_read = datetime.utcnow()
            topicsread.save()
            updated = True

        # No unread posts
        else:
            updated = False

        # Save True/False if the forums tracker has been updated.
        updated = forum.update_read(user, forumsread, topicsread)

        return updated


class Forum(db.Model):
    __tablename__ = "forums"
    __searchable__ = ['title', 'description']

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"),
                            nullable=False)
    title = db.Column(db.String(15), nullable=False)
    description = db.Column(db.String(255))
    position = db.Column(db.Integer, default=1, nullable=False)
    locked = db.Column(db.Boolean, default=False, nullable=False)
    show_moderators = db.Column(db.Boolean, default=False, nullable=False)
    external = db.Column(db.String(63))

    post_count = db.Column(db.Integer, default=0, nullable=False)
    topic_count = db.Column(db.Integer, default=0, nullable=False)

    # One-to-one
    last_post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    last_post = db.relationship("Post", backref="last_post_forum",
                                uselist=False, foreign_keys=[last_post_id])

    # One-to-many
    topics = db.relationship("Topic", backref="forum", lazy="joined",
                             cascade="all, delete-orphan")

    # Many-to-many
    moderators = \
        db.relationship("User", secondary=moderators,
                        primaryjoin=(moderators.c.forum_id == id),
                        backref=db.backref("forummoderator", lazy="dynamic"),
                        lazy="joined")

    # Properties
    @property
    def slug(self):
        """Returns a slugified version from the forum title"""
        return slugify(self.title)

    @property
    def url(self):
        """Returns the url for the forum"""
        return url_for("forum.view_forum", forum_id=self.id, slug=self.slug)

    # Methods
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.id)

    def update_last_post(self):
        """Updates the last post in the forum."""
        last_post = Post.query.\
            filter(Post.topic_id == Topic.id,
                   Topic.forum_id == self.id).\
            order_by(Post.date_created.desc()).\
            first()

        # Last post is none when there are no topics in the forum
        if last_post is not None:

            # a new last post was found in the forum
            if not last_post.id == self.last_post_id:
                self.last_post_id = last_post.id

        # No post found..
        else:
            self.last_post_id = 0

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
        if not user.is_authenticated() or topicsread is None:
            return False

        # fetch the unread posts in the forum
        unread_count = Topic.query.\
            outerjoin(TopicsRead,
                      db.and_(TopicsRead.topic_id == Topic.id,
                              TopicsRead.user_id == user.id)).\
            outerjoin(ForumsRead,
                      db.and_(ForumsRead.forum_id == Topic.forum_id,
                              ForumsRead.user_id == user.id)).\
            filter(Topic.forum_id == self.id,
                   db.or_(TopicsRead.last_read == None,
                          TopicsRead.last_read < Topic.last_updated)).\
            count()

        # No unread topics available - trying to mark the forum as read
        if unread_count == 0:

            if forumsread and forumsread.last_read > topicsread.last_read:
                return False

            # ForumRead Entry exists - Updating it because a new post
            # has been submitted that the user hasn't read.
            elif forumsread:
                forumsread.last_read = datetime.utcnow()
                forumsread.save()
                return True

            # No ForumRead Entry existing - creating one.
            forumsread = ForumsRead()
            forumsread.user_id = user.id
            forumsread.forum_id = self.id
            forumsread.last_read = datetime.utcnow()
            forumsread.save()
            return True

        # Nothing updated, because there are still more than 0 unread topics
        return False

    def save(self, moderators=None):
        """Saves a forum"""
        if moderators is not None:
            for moderator in self.moderators:
                self.moderators.remove(moderator)
            db.session.commit()

            for moderator in moderators:
                if moderator:
                    self.moderators.append(moderator)

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

        # Delete all entries from the ForumsRead and TopicsRead relation
        ForumsRead.query.filter_by(forum_id=self.id).delete()
        TopicsRead.query.filter_by(forum_id=self.id).delete()

        # Update the users post count
        if users:
            users_list = []
            for user in users:
                user.post_count = Post.query.filter_by(user_id=user.id).count()
                users_list.append(user)
            db.session.add_all(users_list)
            db.session.commit()

        return self


class Category(db.Model):
    __tablename__ = "categories"
    __searchable__ = ['title', 'description']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(63), nullable=False)
    description = db.Column(db.String(255))
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
        """Returns the url for the category"""
        return url_for("forum.view_category", category_id=self.id,
                       slug=self.slug)

    # Methods
    def save(self):
        """Saves a category"""

        db.session.add(self)
        db.session.commit()
        return self

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
