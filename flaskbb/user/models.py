# -*- coding: utf-8 -*-
"""
    flaskbb.user.models
    ~~~~~~~~~~~~~~~~~~~~

    This module provides the models for the user.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
from datetime import datetime

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from werkzeug import generate_password_hash, check_password_hash
from flask import current_app, url_for
from flask.ext.login import UserMixin, AnonymousUserMixin
from flaskbb.extensions import db, cache
from flaskbb.utils.settings import flaskbb_config
from flaskbb.forum.models import (Post, Topic, topictracker, TopicsRead,
                                  ForumsRead)


groups_users = db.Table(
    'groups_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('group_id', db.Integer(), db.ForeignKey('groups.id')))


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), unique=True, nullable=False)
    description = db.Column(db.String(80))

    # I bet there is a nicer way for this :P
    admin = db.Column(db.Boolean, default=False, nullable=False)
    super_mod = db.Column(db.Boolean, default=False, nullable=False)
    mod = db.Column(db.Boolean, default=False, nullable=False)
    guest = db.Column(db.Boolean, default=False, nullable=False)
    banned = db.Column(db.Boolean, default=False, nullable=False)

    editpost = db.Column(db.Boolean, default=True, nullable=False)
    deletepost = db.Column(db.Boolean, default=False, nullable=False)
    deletetopic = db.Column(db.Boolean, default=False, nullable=False)
    locktopic = db.Column(db.Boolean, default=False, nullable=False)
    movetopic = db.Column(db.Boolean, default=False, nullable=False)
    mergetopic = db.Column(db.Boolean, default=False, nullable=False)
    posttopic = db.Column(db.Boolean, default=True, nullable=False)
    postreply = db.Column(db.Boolean, default=True, nullable=False)

    # Methods
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {})>".format(self.__class__.__name__, self.id)

    def save(self):
        """Saves a group"""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Deletes a group"""
        db.session.delete(self)
        db.session.commit()
        return self


class User(db.Model, UserMixin):
    __tablename__ = "users"
    __searchable__ = ['username', 'email']

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(63), unique=True, nullable=False)
    _password = db.Column('password', db.String(80), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow())
    lastseen = db.Column(db.DateTime, default=datetime.utcnow())
    birthday = db.Column(db.DateTime)
    gender = db.Column(db.String(1))
    website = db.Column(db.String(63))
    location = db.Column(db.String(63))
    signature = db.Column(db.String(255))
    avatar = db.Column(db.String(63))
    notes = db.Column(db.Text)

    theme = db.Column(db.String(15))

    posts = db.relationship("Post", backref="user", lazy="dynamic")
    topics = db.relationship("Topic", backref="user", lazy="dynamic")

    post_count = db.Column(db.Integer, default=0)

    primary_group_id = db.Column(db.Integer, db.ForeignKey('groups.id'),
                                 nullable=False)

    primary_group = db.relationship('Group', lazy="joined",
                                    backref="user_group", uselist=False,
                                    foreign_keys=[primary_group_id])

    secondary_groups = \
        db.relationship('Group',
                        secondary=groups_users,
                        primaryjoin=(groups_users.c.user_id == id),
                        backref=db.backref('users', lazy='dynamic'),
                        lazy='dynamic')

    tracked_topics = \
        db.relationship("Topic", secondary=topictracker,
                        primaryjoin=(topictracker.c.user_id == id),
                        backref=db.backref("topicstracked", lazy="dynamic"),
                        lazy="dynamic")

    # Properties
    @property
    def last_post(self):
        """Returns the latest post from the user"""

        return Post.query.filter(Post.user_id == self.id).\
            order_by(Post.date_created.desc()).first()

    @property
    def url(self):
        """Returns the url for the user"""
        return url_for("user.profile", username=self.username)

    # Methods
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "Username: %s" % self.username

    def _get_password(self):
        """Returns the hashed password"""
        return self._password

    def _set_password(self, password):
        """Generates a password hash for the provided password"""
        self._password = generate_password_hash(password)

    # Hide password encryption by exposing password field only.
    password = db.synonym('_password',
                          descriptor=property(_get_password,
                                              _set_password))

    def check_password(self, password):
        """Check passwords. If passwords match it returns true, else false"""

        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    @classmethod
    def authenticate(cls, login, password):
        """A classmethod for authenticating users
        It returns true if the user exists and has entered a correct password

        :param login: This can be either a username or a email address.

        :param password: The password that is connected to username and email.
        """

        user = cls.query.filter(db.or_(User.username == login,
                                       User.email == login)).first()

        if user:
            authenticated = user.check_password(password)
        else:
            authenticated = False
        return user, authenticated

    def _make_token(self, data, timeout):
        s = Serializer(current_app.config['SECRET_KEY'], timeout)
        return s.dumps(data)

    def _verify_token(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        data = None
        expired, invalid = False, False
        try:
            data = s.loads(token)
        except SignatureExpired:
            expired = True
        except Exception:
            invalid = True
        return expired, invalid, data

    def make_reset_token(self, expiration=3600):
        """Creates a reset token. The duration can be configured through the
        expiration parameter.

        :param expiration: The time in seconds how long the token is valid.
        """
        return self._make_token({'id': self.id, 'op': 'reset'}, expiration)

    def verify_reset_token(self, token):
        """Verifies a reset token. It returns three boolean values based on
        the state of the token (expired, invalid, data)

        :param token: The reset token that should be checked.
        """

        expired, invalid, data = self._verify_token(token)
        if data and data.get('id') == self.id and data.get('op') == 'reset':
            data = True
        else:
            data = False
        return expired, invalid, data

    def all_topics(self, page):
        """Returns a paginated result with all topics the user has created."""

        return Topic.query.filter(Topic.user_id == self.id).\
            filter(Post.topic_id == Topic.id).\
            order_by(Post.id.desc()).\
            paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)

    def all_posts(self, page):
        """Returns a paginated result with all posts the user has created."""

        return Post.query.filter(Post.user_id == self.id).\
            paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)

    def track_topic(self, topic):
        """Tracks the specified topic

        :param topic: The topic which should be added to the topic tracker.
        """

        if not self.is_tracking_topic(topic):
            self.tracked_topics.append(topic)
            return self

    def untrack_topic(self, topic):
        """Untracks the specified topic

        :param topic: The topic which should be removed from the
                      topic tracker.
        """

        if self.is_tracking_topic(topic):
            self.tracked_topics.remove(topic)
            return self

    def is_tracking_topic(self, topic):
        """Checks if the user is already tracking this topic

        :param topic: The topic which should be checked.
        """

        return self.tracked_topics.filter(
            topictracker.c.topic_id == topic.id).count() > 0

    def add_to_group(self, group):
        """Adds the user to the `group` if he isn't in it.

        :param group: The group which should be added to the user.
        """

        if not self.in_group(group):
            self.secondary_groups.append(group)
            return self

    def remove_from_group(self, group):
        """Removes the user from the `group` if he is in it.

        :param group: The group which should be removed from the user.
        """

        if self.in_group(group):
            self.secondary_groups.remove(group)
            return self

    def in_group(self, group):
        """Returns True if the user is in the specified group

        :param group: The group which should be checked.
        """

        return self.secondary_groups.filter(
            groups_users.c.group_id == group.id).count() > 0

    @cache.memoize(timeout=sys.maxint)
    def get_permissions(self, exclude=None):
        """Returns a dictionary with all the permissions the user has.

        :param exclude: a list with excluded permissions. default is None.
        """

        exclude = exclude or []
        exclude.extend(['id', 'name', 'description'])

        perms = {}
        groups = self.secondary_groups.all()
        groups.append(self.primary_group)
        for group in groups:
            for c in group.__table__.columns:
                # try if the permission already exists in the dictionary
                # and if the permission is true, set it to True
                try:
                    if not perms[c.name] and getattr(group, c.name):
                        perms[c.name] = True

                # if the permission doesn't exist in the dictionary
                # add it to the dictionary
                except KeyError:
                    # if the permission is in the exclude list,
                    # skip to the next permission
                    if c.name in exclude:
                        continue
                    perms[c.name] = getattr(group, c.name)
        return perms

    def invalidate_cache(self):
        """Invalidates this objects cached metadata."""

        cache.delete_memoized(self.get_permissions, self)

    def save(self, groups=None):
        """Saves a user. If a list with groups is provided, it will add those
        to the secondary groups from the user.

        :param groups: A list with groups that should be added to the
                       secondary groups from user.
        """

        if groups:
            # TODO: Only remove/add groups that are selected
            secondary_groups = self.secondary_groups.all()
            for group in secondary_groups:
                self.remove_from_group(group)
            db.session.commit()

            for group in groups:
                # Do not add the primary group to the secondary groups
                if group.id == self.primary_group_id:
                    continue
                self.add_to_group(group)

            self.invalidate_cache()

        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Deletes the User."""

        # This isn't done automatically...
        PrivateMessage.query.filter_by(user_id=self.id).delete()
        ForumsRead.query.filter_by(user_id=self.id).delete()
        TopicsRead.query.filter_by(user_id=self.id).delete()

        db.session.delete(self)
        db.session.commit()

        return self


class Guest(AnonymousUserMixin):
    def get_permissions(self, exclude=None):
        """Returns a dictionary with all permissions the user has"""
        exclude = exclude or []
        exclude.extend(['id', 'name', 'description'])

        perms = {}
        # Get the Guest group
        group = Group.query.filter_by(guest=True).first()
        for c in group.__table__.columns:
            if c.name in exclude:
                continue
            perms[c.name] = getattr(group, c.name)
        return perms


class PrivateMessage(db.Model):
    __tablename__ = "privatemessages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    subject = db.Column(db.String(63))
    message = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    trash = db.Column(db.Boolean, nullable=False, default=False)
    draft = db.Column(db.Boolean, nullable=False, default=False)
    unread = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship("User", backref="pms", lazy="joined",
                           foreign_keys=[user_id])
    from_user = db.relationship("User", lazy="joined",
                                foreign_keys=[from_user_id])
    to_user = db.relationship("User", lazy="joined", foreign_keys=[to_user_id])

    def save(self, from_user=None, to_user=None, user_id=None, draft=False):
        """Saves a private message.

        :param from_user: The user who has sent the message

        :param to_user: The user who should recieve the message

        :param user_id: The senders user id

        :param draft: If the message is a draft
        """

        if self.id:
            db.session.add(self)
            db.session.commit()
            return self

        if draft:
            self.draft = True

        # Add the message to the user's pm box
        self.user_id = user_id
        self.from_user_id = from_user
        self.to_user_id = to_user
        self.date_created = datetime.utcnow()

        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Deletes a private message"""

        db.session.delete(self)
        db.session.commit()
        return self
