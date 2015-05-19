# -*- coding: utf-8 -*-
"""
    flaskbb.user.models
    ~~~~~~~~~~~~~~~~~~~~

    This module provides the models for the user.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, url_for
from flask_login import UserMixin, AnonymousUserMixin

from flaskbb._compat import max_integer, string_types
from flaskbb.extensions import db, cache
from flaskbb.utils.settings import flaskbb_config
from flaskbb.forum.models import (Post, Topic, topictracker, TopicsRead,
                                  ForumsRead)
from flaskbb.message.models import Conversation


roles_groups = db.Table(
    'roles_groups',
    db.Column('group_id', db.Integer(), db.ForeignKey('groups.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('roles.id'))
)


groups_users = db.Table(
    'groups_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('group_id', db.Integer(), db.ForeignKey('groups.id'))
)


class Group(db.Model):
    """Users belong to groups and roles belong to groups. A user can be in more
    than one group."""

    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)

    roles = db.relationship('Role', secondary=roles_groups,
                            backref=db.backref('groups', lazy='dynamic'))

    # Methods
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.id)

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

    @classmethod
    def selectable_groups_choices(cls):
        return Group.query.order_by(Group.name.asc()).with_entities(
            Group.id, Group.name
        ).all()

    @classmethod
    def get_guest_group(cls):
        return Group.query.filter(Role.name == "guest").first()


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __eq__(self, other):
        return (self.name == other or
                self.name == getattr(other, 'name', None))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.name)

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self


class User(db.Model, UserMixin):
    __tablename__ = "users"
    __searchable__ = ['username', 'email']

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    _password = db.Column('password', db.String(120), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow())
    lastseen = db.Column(db.DateTime, default=datetime.utcnow())
    birthday = db.Column(db.DateTime)
    gender = db.Column(db.String(10))
    website = db.Column(db.String(200))
    location = db.Column(db.String(100))
    signature = db.Column(db.Text)
    avatar = db.Column(db.String(200))
    notes = db.Column(db.Text)

    theme = db.Column(db.String(15))
    language = db.Column(db.String(15), default="en")

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

    @property
    def roles(self):
        """Returns the roles for the user"""
        return self.get_roles()

    @property
    def days_registered(self):
        """Returns the amount of days the user is registered."""
        days_registered = (datetime.utcnow() - self.date_joined).days
        if not days_registered:
            return 1
        return days_registered

    @property
    def topic_count(self):
        """Returns the thread count"""
        return Topic.query.filter(Topic.user_id == self.id).count()

    @property
    def posts_per_day(self):
        """Returns the posts per day count"""
        return round((float(self.post_count) / float(self.days_registered)), 1)

    @property
    def topics_per_day(self):
        """Returns the topics per day count"""
        return round((float(self.topic_count) / float(self.days_registered)), 1)

    @property
    def groups(self):
        """Returns user groups"""
        return self.get_groups()

    # Methods
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.username)

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

    @cache.memoize(timeout=max_integer)
    def get_groups(self):
        """Returns a list of all groups the user is in."""
        return [self.primary_group] + list(self.secondary_groups)

    @cache.memoize(timeout=max_integer)
    def get_roles(self):
        """Returns a set with all roles the user has.

        :param exclude: a list with excluded permissions. default is None.
        """

        roles = set()
        groups = self.secondary_groups.all()
        groups.append(self.primary_group)
        for group in groups:
            # collect the roles
            roles.update(set(group.roles))

        return roles

    def has_role(self, role):
        """Returns `True` if the user identifies with the specified role.

        :param role: A role name or `Role` instance"""
        if isinstance(role, string_types):
            return role in (role.name for role in self.roles)
        else:
            return role in self.roles

    def invalidate_cache(self):
        """Invalidates this objects cached metadata."""
        cache.delete_memoized(self.get_permissions, self)
        cache.delete_memoized(self.get_roles, self)

    def ban(self):
        """Bans the user. Returns True upon success."""

        if not self.get_permissions()['banned']:
            banned_group = Group.query.filter(
                Group.banned == True
            ).first()

            self.primary_group_id = banned_group.id
            self.save()
            self.invalidate_cache()
            return True
        return False

    def unban(self):
        """Unbans the user. Returns True upon success."""

        if self.get_permissions()['banned']:
            member_group = Group.query.filter(
                Group.admin == False,
                Group.super_mod == False,
                Group.mod == False,
                Group.guest == False,
                Group.banned == False
            ).first()

            self.primary_group_id = member_group.id
            self.save()
            self.invalidate_cache()
            return True
        return False

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
        Conversation.query.filter_by(user_id=self.id).delete()
        ForumsRead.query.filter_by(user_id=self.id).delete()
        TopicsRead.query.filter_by(user_id=self.id).delete()

        # This should actually be handeld by the dbms.. but dunno why it doesnt
        # work here
        from flaskbb.forum.models import Forum

        last_post_forums = Forum.query.\
            filter_by(last_post_user_id=self.id).all()

        for forum in last_post_forums:
            forum.last_post_user_id = None
            forum.save()

        db.session.delete(self)
        db.session.commit()

        return self


class Guest(AnonymousUserMixin):
    @property
    def roles(self):
        return self.get_roles()

    @cache.memoize(timeout=max_integer)
    def get_roles(self):
        """Returns a set with all roles the user has"""

        # Get the Guest group
        group = Group.query.filter_by(guest=True).first()
        return set(group.roles)

    def has_role(self, *args):
        """Returns `False`"""
        return False

    @classmethod
    def invalidate_cache(cls):
        """Invalidates this objects cached metadata."""

        cache.delete_memoized(cls.get_permissions, cls)
