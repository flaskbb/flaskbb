# -*- coding: utf-8 -*-
"""
    flaskbb.user.models
    ~~~~~~~~~~~~~~~~~~~

    This module provides the models for the user.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging

from flask import url_for
from flask_login import AnonymousUserMixin, UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from flaskbb.deprecation import deprecated
from flaskbb.exceptions import AuthenticationError
from flaskbb.extensions import cache, db
from flaskbb.forum.models import Forum, Post, Topic, topictracker
from flaskbb.utils.database import CRUDMixin, UTCDateTime, make_comparable
from flaskbb.utils.helpers import time_utcnow
from flaskbb.utils.settings import flaskbb_config

logger = logging.getLogger(__name__)


groups_users = db.Table(
    'groups_users',
    db.Column('user_id', db.Integer,
              db.ForeignKey('users.id', ondelete="CASCADE"),
              nullable=False),
    db.Column('group_id', db.Integer,
              db.ForeignKey('groups.id', ondelete="CASCADE"),
              nullable=False)
)


@make_comparable
class Group(db.Model, CRUDMixin):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Group types
    admin = db.Column(db.Boolean, default=False, nullable=False)
    super_mod = db.Column(db.Boolean, default=False, nullable=False)
    mod = db.Column(db.Boolean, default=False, nullable=False)
    guest = db.Column(db.Boolean, default=False, nullable=False)
    banned = db.Column(db.Boolean, default=False, nullable=False)

    # Moderator permissions (only available when the user a moderator)
    mod_edituser = db.Column(db.Boolean, default=False, nullable=False)
    mod_banuser = db.Column(db.Boolean, default=False, nullable=False)

    # User permissions
    editpost = db.Column(db.Boolean, default=True, nullable=False)
    deletepost = db.Column(db.Boolean, default=False, nullable=False)
    deletetopic = db.Column(db.Boolean, default=False, nullable=False)
    posttopic = db.Column(db.Boolean, default=True, nullable=False)
    postreply = db.Column(db.Boolean, default=True, nullable=False)
    viewhidden = db.Column(db.Boolean, default=False, nullable=False)
    makehidden = db.Column(db.Boolean, default=False, nullable=False)

    # Methods
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {} {}>".format(self.__class__.__name__, self.id, self.name)

    @classmethod
    def selectable_groups_choices(cls):
        return Group.query.order_by(Group.name.asc()).with_entities(
            Group.id, Group.name
        ).all()

    @classmethod
    def get_guest_group(cls):
        return cls.query.filter(cls.guest == True).first()

    @classmethod
    def get_member_group(cls):
        """Returns the first member group."""
        # This feels ugly..
        return cls.query.filter(cls.admin == False, cls.super_mod == False,
                                cls.mod == False, cls.guest == False,
                                cls.banned == False).first()


class User(db.Model, UserMixin, CRUDMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    _password = db.Column('password', db.String(120), nullable=False)
    date_joined = db.Column(UTCDateTime(timezone=True), default=time_utcnow,
                            nullable=False)
    lastseen = db.Column(UTCDateTime(timezone=True), default=time_utcnow,
                         nullable=True)
    birthday = db.Column(db.DateTime, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    signature = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    last_failed_login = db.Column(UTCDateTime(timezone=True), nullable=True)
    login_attempts = db.Column(db.Integer, default=0, nullable=False)
    activated = db.Column(db.Boolean, default=False, nullable=False)

    theme = db.Column(db.String(15), nullable=True)
    language = db.Column(db.String(15), default="en", nullable=True)

    post_count = db.Column(db.Integer, default=0)

    primary_group_id = db.Column(db.Integer, db.ForeignKey('groups.id'),
                                 nullable=False)

    posts = db.relationship(
        "Post",
        backref="user",
        primaryjoin="User.id == Post.user_id",
        lazy="dynamic"
    )

    topics = db.relationship(
        "Topic",
        backref="user",
        primaryjoin="User.id == Topic.user_id",
        lazy="dynamic"
    )

    primary_group = db.relationship(
        "Group",
        backref="user_group",
        uselist=False,
        lazy="joined",
        foreign_keys=[primary_group_id]
    )

    secondary_groups = db.relationship(
        "Group",
        secondary=groups_users,
        primaryjoin=(groups_users.c.user_id == id),
        backref=db.backref("users", lazy="dynamic"),
        lazy="dynamic"
    )

    tracked_topics = db.relationship(
        "Topic",
        secondary=topictracker,
        primaryjoin=(topictracker.c.user_id == id),
        backref=db.backref("topicstracked", lazy="dynamic"),
        lazy="dynamic",
        single_parent=True
    )

    # Properties
    @property
    def is_active(self):
        """Returns the state of the account.
        If the ``ACTIVATE_ACCOUNT`` option has been disabled, it will always
        return ``True``. Is the option activated, it will, depending on the
        state of the account, either return ``True`` or ``False``.
        """
        if flaskbb_config["ACTIVATE_ACCOUNT"]:
            if self.activated:
                return True
            return False

        return True

    @property
    def last_post(self):
        """Returns the latest post from the user."""
        return Post.query.filter(Post.user_id == self.id).\
            order_by(Post.date_created.desc()).first()

    @property
    def url(self):
        """Returns the url for the user."""
        return url_for("user.profile", username=self.username)

    @property
    def permissions(self):
        """Returns the permissions for the user."""
        return self.get_permissions()

    @property
    def groups(self):
        """Returns the user groups."""
        return self.get_groups()

    @property
    def days_registered(self):
        """Returns the amount of days the user is registered."""
        days_registered = (time_utcnow() - self.date_joined).days
        if not days_registered:
            return 1
        return days_registered

    @property
    def topic_count(self):
        """Returns the thread count."""
        return Topic.query.filter(Topic.user_id == self.id).count()

    @property
    def posts_per_day(self):
        """Returns the posts per day count."""
        return round((float(self.post_count) / float(self.days_registered)), 1)

    @property
    def topics_per_day(self):
        """Returns the topics per day count."""
        return round(
            (float(self.topic_count) / float(self.days_registered)), 1
        )

    # Methods
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.username)

    def _get_password(self):
        """Returns the hashed password."""
        return self._password

    def _set_password(self, password):
        """Generates a password hash for the provided password."""
        if not password:
            return
        self._password = generate_password_hash(password)

    # Hide password encryption by exposing password field only.
    password = db.synonym('_password',
                          descriptor=property(_get_password,
                                              _set_password))

    def check_password(self, password):
        """Check passwords. If passwords match it returns true, else false."""

        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    @classmethod
    @deprecated("Use authentication services instead.")
    def authenticate(cls, login, password):
        """A classmethod for authenticating users.
        It returns the user object if the user/password combination is ok.
        If the user has entered too often a wrong password, he will be locked
        out of his account for a specified time.

        :param login: This can be either a username or a email address.
        :param password: The password that is connected to username and email.
        """
        user = cls.query.filter(db.or_(User.username == login,
                                       User.email == login)).first()

        if user is not None:
            if user.check_password(password):
                # reset them after a successful login attempt
                user.login_attempts = 0
                user.save()
                return user

            # user exists, wrong password
            # never had a bad login before
            if user.login_attempts is None:
                user.login_attempts = 1
            else:
                user.login_attempts += 1
            user.last_failed_login = time_utcnow()
            user.save()

        # protection against account enumeration timing attacks
        check_password_hash("dummy password", password)

        raise AuthenticationError

    def recalculate(self):
        """Recalculates the post count from the user."""
        self.post_count = Post.query.filter_by(user_id=self.id).count()
        self.save()
        return self

    def all_topics(self, page, viewer):
        """Topics made by a given user, most recent first.

        :param page: The page which should be displayed.
        :param viewer: The user who is viewing the page. Only posts
                       accessible to the viewer will be returned.
        :rtype: flask_sqlalchemy.Pagination
        """
        group_ids = [g.id for g in viewer.groups]
        topics = Topic.query.\
            filter(Topic.user_id == self.id,
                   Forum.id == Topic.forum_id,
                   Forum.groups.any(Group.id.in_(group_ids))).\
            order_by(Topic.id.desc()).\
            paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)
        return topics

    def all_posts(self, page, viewer):
        """Posts made by a given user, most recent first.

        :param page: The page which should be displayed.
        :param viewer: The user who is viewing the page. Only posts
                       accessible to the viewer will be returned.
        :rtype: flask_sqlalchemy.Pagination
        """
        group_ids = [g.id for g in viewer.groups]
        posts = Post.query.\
            filter(Post.user_id == self.id,
                   Post.topic_id == Topic.id,
                   Topic.forum_id == Forum.id,
                   Forum.groups.any(Group.id.in_(group_ids))).\
            order_by(Post.id.desc()).\
            paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)
        return posts

    def track_topic(self, topic):
        """Tracks the specified topic.

        :param topic: The topic which should be added to the topic tracker.
        """
        if not self.is_tracking_topic(topic):
            self.tracked_topics.append(topic)
            return self

    def untrack_topic(self, topic):
        """Untracks the specified topic.

        :param topic: The topic which should be removed from the
                      topic tracker.
        """
        if self.is_tracking_topic(topic):
            self.tracked_topics.remove(topic)
            return self

    def is_tracking_topic(self, topic):
        """Checks if the user is already tracking this topic.

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
        """Returns True if the user is in the specified group.

        :param group: The group which should be checked.
        """
        return self.secondary_groups.filter(
            groups_users.c.group_id == group.id).count() > 0

    @cache.memoize()
    def get_groups(self):
        """Returns all the groups the user is in."""
        return [self.primary_group] + list(self.secondary_groups)

    @cache.memoize()
    def get_permissions(self, exclude=None):
        """Returns a dictionary with all permissions the user has"""
        if exclude:
            exclude = set(exclude)
        else:
            exclude = set()
        exclude.update(['id', 'name', 'description'])

        perms = {}
        # Get the Guest group
        for group in self.groups:
            columns = set(group.__table__.columns.keys()) - set(exclude)
            for c in columns:
                perms[c] = getattr(group, c) or perms.get(c, False)
        return perms

    def invalidate_cache(self):
        """Invalidates this objects cached metadata."""
        cache.delete_memoized(self.get_permissions, self)
        cache.delete_memoized(self.get_groups, self)

    def ban(self):
        """Bans the user. Returns True upon success."""
        if not self.get_permissions()['banned']:
            banned_group = Group.query.filter(
                Group.banned == True
            ).first()

            self.primary_group = banned_group
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

            self.primary_group = member_group
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
        if groups is not None:
            # TODO: Only remove/add groups that are selected
            secondary_groups = self.secondary_groups.all()
            for group in secondary_groups:
                self.remove_from_group(group)
            db.session.commit()

            for group in groups:
                # Do not add the primary group to the secondary groups
                if group == self.primary_group:
                    continue
                self.add_to_group(group)

            self.invalidate_cache()

        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Deletes the User."""
        db.session.delete(self)
        db.session.commit()

        return self


class Guest(AnonymousUserMixin):
    @property
    def permissions(self):
        return self.get_permissions()

    @property
    def groups(self):
        return self.get_groups()

    @cache.memoize()
    def get_groups(self):
        return Group.query.filter(Group.guest == True).all()

    @cache.memoize()
    def get_permissions(self, exclude=None):
        """Returns a dictionary with all permissions the user has"""
        if exclude:
            exclude = set(exclude)
        else:
            exclude = set()
        exclude.update(['id', 'name', 'description'])

        perms = {}
        # Get the Guest group
        for group in self.groups:
            columns = set(group.__table__.columns.keys()) - set(exclude)
            for c in columns:
                perms[c] = getattr(group, c) or perms.get(c, False)
        return perms

    @classmethod
    def invalidate_cache(cls):
        """Invalidates this objects cached metadata."""
        cache.delete_memoized(cls.get_permissions, cls)
