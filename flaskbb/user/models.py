# -*- coding: utf-8 -*-
"""
flaskbb.user.models
~~~~~~~~~~~~~~~~~~~

This module provides the models for the user.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
from typing import override

from flask import url_for
from flask.helpers import abort
from flask_login import AnonymousUserMixin, UserMixin
from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import (
    Mapped,
    WriteOnlyMapped,
    mapped_column,
    relationship,
    synonym,
)
from sqlalchemy.types import DateTime, String, Text
from werkzeug.security import check_password_hash, generate_password_hash

from flaskbb.extensions import cache, db
from flaskbb.forum.models import Forum, Post, Topic, topictracker
from flaskbb.utils.database import CRUDMixin, UTCDateTime, make_comparable
from flaskbb.utils.helpers import time_utcnow
from flaskbb.utils.settings import flaskbb_config

logger = logging.getLogger(__name__)


groups_users = db.Table(
    "groups_users",
    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    db.Column(
        "group_id",
        db.Integer,
        db.ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    ),
)


@make_comparable
class Group(db.Model, CRUDMixin):
    __tablename__: str = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Text] = mapped_column(Text, nullable=True)

    # Group types
    admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    super_mod: Mapped[bool] = mapped_column(default=False, nullable=False)
    mod: Mapped[bool] = mapped_column(default=False, nullable=False)
    guest: Mapped[bool] = mapped_column(default=False, nullable=False)
    banned: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Moderator permissions (only available when the user a moderator)
    mod_edituser: Mapped[bool] = mapped_column(default=False, nullable=False)
    mod_banuser: Mapped[bool] = mapped_column(default=False, nullable=False)

    # User permissions
    editpost: Mapped[bool] = mapped_column(default=True, nullable=False)
    deletepost: Mapped[bool] = mapped_column(default=False, nullable=False)
    deletetopic: Mapped[bool] = mapped_column(default=False, nullable=False)
    posttopic: Mapped[bool] = mapped_column(default=True, nullable=False)
    postreply: Mapped[bool] = mapped_column(default=True, nullable=False)
    viewhidden: Mapped[bool] = mapped_column(default=False, nullable=False)
    makehidden: Mapped[bool] = mapped_column(default=False, nullable=False)

    @override
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {} {}>".format(self.__class__.__name__, self.id, self.name)

    @classmethod
    def selectable_groups_choices(cls):
        return db.session.execute(
            db.select(cls.id, cls.name).order_by(cls.name.asc())
        ).all()

    @classmethod
    def get_guest_group(cls):
        return db.session.execute(
            db.select(cls).filter(cls.guest.is_(True))
        ).scalar_one_or_none()

    @classmethod
    def get_member_group(cls):
        """Returns the first member group."""
        return db.session.execute(
            db.select(cls).filter(
                cls.admin.is_(False),
                cls.super_mod.is_(False),
                cls.mod.is_(False),
                cls.guest.is_(False),
                cls.banned.is_(False),
            )
        ).scalar_one_or_none()


class User(db.Model, UserMixin, CRUDMixin):
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    _password: Mapped[str] = mapped_column("password", String(120), nullable=False)
    date_joined: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime(timezone=True), default=time_utcnow, nullable=False
    )
    lastseen: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime(timezone=True), default=time_utcnow, nullable=True
    )
    birthday: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=True)
    website: Mapped[str] = mapped_column(String(200), nullable=True)
    location: Mapped[str] = mapped_column(String(100), nullable=True)
    signature: Mapped[Text] = mapped_column(Text, nullable=True)
    avatar: Mapped[str] = mapped_column(String(200), nullable=True)
    notes: Mapped[Text] = mapped_column(Text, nullable=True)

    last_failed_login: Mapped[UTCDateTime] = mapped_column(
        UTCDateTime(timezone=True), nullable=True
    )
    login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    activated: Mapped[bool] = mapped_column(default=False, nullable=False)

    theme: Mapped[str] = mapped_column(String(15), nullable=True)
    language: Mapped[str] = mapped_column(String(15), default="en", nullable=True)

    post_count: Mapped[int] = mapped_column(default=0)

    primary_group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"), nullable=False
    )

    posts: Mapped[list[Post]] = relationship(
        "Post",
        primaryjoin="User.id == Post.user_id",
        lazy="dynamic",
    )

    topics: Mapped[list[Topic]] = relationship(
        "Topic",
        primaryjoin="User.id == Topic.user_id",
        lazy="dynamic",
    )

    primary_group: Mapped[Group] = relationship(
        "Group",
        uselist=False,
        lazy="joined",
        foreign_keys=[primary_group_id],
    )

    secondary_groups: Mapped[list[Group]] = relationship(
        "Group",
        secondary=groups_users,
        primaryjoin=(groups_users.c.user_id == id),
        lazy="dynamic",
    )

    tracked_topics: WriteOnlyMapped["Topic"] = relationship(
        secondary=topictracker,
        primaryjoin=(topictracker.c.user_id == id),
        lazy="dynamic",
        single_parent=True,
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
        return db.session.execute(
            db.select(Post)
            .filter(Post.user_id == self.id)
            .order_by(Post.date_created.desc())
        ).scalar_one_or_none()

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
    def days_registered(self) -> int:
        """Returns the amount of days the user is registered."""
        days_registered: int | None = (time_utcnow() - self.date_joined).days
        if not days_registered:
            return 1
        return days_registered

    @property
    def topic_count(self):
        """Returns the thread count."""
        return db.session.execute(
            db.select(db.func.count())
            .select_from(Topic)
            .filter(Topic.user_id == self.id)
        ).scalar_one()

    @property
    def posts_per_day(self):
        """Returns the posts per day count."""
        return round((float(self.post_count) / float(self.days_registered)), 1)

    @property
    def topics_per_day(self):
        """Returns the topics per day count."""
        return round((float(self.topic_count) / float(self.days_registered)), 1)

    # Methods
    @override
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return "<{} {}>".format(self.__class__.__name__, self.username)

    def _get_password(self):
        """Returns the hashed password."""
        return self._password

    def _set_password(self, password: str):
        """Generates a password hash for the provided password."""
        if not password:
            return
        self._password = generate_password_hash(password)

    # Hide password encryption by exposing password field only.
    password = synonym("_password", descriptor=property(_get_password, _set_password))

    def check_password(self, password: str):
        """Check passwords. If passwords match it returns true, else false."""

        if self.password is None:
            return False
        return check_password_hash(self.password, password)

    def recalculate(self):
        """Recalculates the post count from the user."""
        self.post_count = db.session.execute(
            db.select(db.func.count()).select_from(Post).filter_by(user_id=self.id)
        ).scalar_one()
        self.save()
        return self

    def all_topics(self, page: int, viewer: "User"):
        """Topics made by a given user, most recent first.

        :param page: The page which should be displayed.
        :param viewer: The user who is viewing the page. Only posts
                       accessible to the viewer will be returned.
        :rtype: flask_sqlalchemy.Pagination
        """
        group_ids = [g.id for g in viewer.groups]
        stmt = (
            db.select(Topic)
            .where(
                Topic.user_id == self.id,
                Forum.groups.any(Group.id.in_(group_ids)),
            )
            .order_by(Topic.id.desc())
        )
        topics = db.paginate(
            stmt, page=page, per_page=flaskbb_config["TOPICS_PER_PAGE"]
        )
        return topics

    def all_posts(self, page: int, viewer: "User"):
        """Posts made by a given user, most recent first.

        :param page: The page which should be displayed.
        :param viewer: The user who is viewing the page. Only posts
                       accessible to the viewer will be returned.
        :rtype: flask_sqlalchemy.Pagination
        """
        group_ids = [g.id for g in viewer.groups]
        stmt = (
            db.select(Post)
            .where(
                Post.user_id == self.id,
                Forum.groups.any(Group.id.in_(group_ids)),
            )
            .order_by(Post.id.desc())
        )
        posts = db.paginate(stmt, page=page, per_page=flaskbb_config["TOPICS_PER_PAGE"])
        return posts

    def track_topic(self, topic: Topic):
        """Tracks the specified topic.

        :param topic: The topic which should be added to the topic tracker.
        """
        if not self.is_tracking_topic(topic):
            self.tracked_topics.add(topic)
            return self

    def untrack_topic(self, topic: Topic):
        """Untracks the specified topic.

        :param topic: The topic which should be removed from the
                      topic tracker.
        """
        if self.is_tracking_topic(topic):
            self.tracked_topics.remove(topic)
            return self

    def is_tracking_topic(self, topic: Topic):
        """Checks if the user is already tracking this topic.

        :param topic: The topic which should be checked.
        """
        stmt = self.tracked_topics.select().where(topictracker.c.topic_id == topic.id)
        return db.session.execute(db.select(stmt.exists())).scalar()

    def add_to_group(self, group: Group):
        """Adds the user to the `group` if he isn't in it.

        :param group: The group which should be added to the user.
        """
        if not self.in_group(group):
            self.secondary_groups.add(group)
            return self

    def remove_from_group(self, group: Group):
        """Removes the user from the `group` if he is in it.

        :param group: The group which should be removed from the user.
        """
        if self.in_group(group):
            self.secondary_groups.remove(group)
            return self

    def in_group(self, group: Group):
        """Returns True if the user is in the specified group.

        :param group: The group which should be checked.
        """
        stmt = self.secondary_groups.select().filter(
            groups_users.c.group_id == group.id
        )
        return db.session.execute(db.select(stmt.exists())).scalar()

    @cache.memoize()
    def get_groups(self):
        """Returns all the groups the user is in."""
        return [self.primary_group] + list(self.secondary_groups)

    @cache.memoize()
    def get_permissions(self, exclude: set[str] | None = None):
        """Returns a dictionary with all permissions the user has"""
        if exclude:
            exclude = set(exclude)
        else:
            exclude = set()
        exclude.update(["id", "name", "description"])

        perms: dict[str, bool] = {}
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
        if not self.get_permissions()["banned"]:
            banned_group = db.session.execute(
                db.select(Group).filter(Group.banned.is_(True))
            ).scalar_one_or_none()

            if not banned_group:
                abort(404)

            self.primary_group = banned_group
            self.save()
            self.invalidate_cache()
            return True
        return False

    def unban(self):
        """Unbans the user. Returns True upon success."""
        if self.get_permissions()["banned"]:
            member_group = db.session.execute(
                db.select(Group).filter(
                    Group.admin.is_(False),
                    Group.super_mod.is_(False),
                    Group.mod.is_(False),
                    Group.guest.is_(False),
                    Group.banned.is_(False),
                )
            ).scalar_one_or_none()

            if not member_group:
                abort(404)

            self.primary_group = member_group
            self.save()
            self.invalidate_cache()
            return True
        return False

    @override
    def save(self, groups: list[Group] | None = None) -> "User":
        """Saves a user. If a list with groups is provided, it will add those
        to the secondary groups from the user.

        :param groups: A list with groups that should be added to the
                       secondary groups from user.
        """
        if groups is not None:
            # TODO: Only remove/add groups that are selected
            with db.session.no_autoflush:
                secondary_groups = (
                    db.session.execute(self.secondary_groups.select()).scalars().all()
                )

                for group in secondary_groups:
                    self.remove_from_group(group)

            for group in groups:
                # Do not add the primary group to the secondary groups
                if group == self.primary_group:
                    continue
                self.add_to_group(group)

            self.invalidate_cache()

        db.session.add(self)
        db.session.commit()
        return self

    @override
    def delete(self) -> "User":
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
        stmt = db.select(Group).where(Group.guest == True)
        result = db.session.execute(stmt).scalars().all()
        return result

    @cache.memoize()
    def get_permissions(self, exclude: set[str] | None = None):
        """Returns a dictionary with all permissions the user has"""
        if exclude:
            exclude = set(exclude)
        else:
            exclude = set()
        exclude.update(["id", "name", "description"])

        perms: dict[str, bool] = {}
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
