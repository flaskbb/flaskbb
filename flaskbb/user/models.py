"""
flaskbb.user.models
~~~~~~~~~~~~~~~~~~~

This module provides the models for the user.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import enum
import logging
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import override

import sqlalchemy as sa
from flask import url_for
from flask.helpers import abort
from flask_login import AnonymousUserMixin, UserMixin
from sqlalchemy.orm import (
    DynamicMapped,
    Mapped,
    mapped_column,
    relationship,
    synonym,
    WriteOnlyMapped,
)
from sqlalchemy.types import DateTime, String, Text
from werkzeug.security import check_password_hash, generate_password_hash

from flaskbb.core.auth.permissions import UserPermissions
from flaskbb.extensions import cache, db
from flaskbb.forum.models import Forum, Post, Topic, topictracker
from flaskbb.permissions import permission_manager, permission_registry, PermissionLevel
from flaskbb.settings import flaskbb_config
from flaskbb.utils.database import BaseModel, make_comparable, UTCDateTime
from flaskbb.utils.helpers import time_utcnow

logger = logging.getLogger(__name__)


groups_users = sa.Table(
    "groups_users",
    db.metadata,
    sa.Column(
        "user_id",
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column(
        "group_id",
        sa.Integer,
        sa.ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    ),
)


PERMISSIONS_VERSION_KEY = "permissions_version"


class GroupRole(enum.StrEnum):
    GUEST = "guest"
    BANNED = "banned"
    MEMBER = "member"
    MODERATOR = "mod"
    SUPER_MODERATOR = "super_mod"
    ADMINISTRATOR = "admin"

    @property
    def rank(self) -> int:
        """Moderators outrank members, super moderators outrank moderators and
        administrators outrank everyone. Guests and banned users rank as members.
        """
        return {
            GroupRole.MODERATOR: 1,
            GroupRole.SUPER_MODERATOR: 2,
            GroupRole.ADMINISTRATOR: 3,
        }.get(self, 0)


def permissions_version() -> int:
    """The cache generation the permissions of every identity are keyed on."""
    return cache.get(PERMISSIONS_VERSION_KEY) or 0


def invalidate_all_permissions() -> None:
    """Starts a new cache generation, so every cached permission set is
    recomputed on its next use. Constant time, no matter how many users a
    changed group has.
    """
    cache.set(PERMISSIONS_VERSION_KEY, permissions_version() + 1, timeout=0)
    permission_manager.forget()


@cache.memoize()
def _load_groups(version: int) -> dict[int, "Group"]:
    return {group.id: group for group in db.session.scalars(sa.select(Group))}


@cache.memoize()
def _load_group_permissions(version: int) -> dict[tuple[int, str], PermissionLevel]:
    return {
        (group_id, key): level
        for group_id, key, level in db.session.execute(
            sa.select(GroupPermission.group_id, GroupPermission.permission, GroupPermission.level)
        )
    }


def all_groups() -> dict[int, "Group"]:
    """Every group by id. Groups are few, so one cached load serves every
    identity instead of a query per user.
    """
    return _load_groups(permissions_version())


def groups_by_id(group_ids: Iterable[int]) -> list["Group"]:
    group_ids = list(group_ids)
    groups = all_groups()
    if any(group_id not in groups for group_id in group_ids):
        # a group this process has not seen yet, e.g. created by another
        # process while the cache is not shared
        cache.delete_memoized(_load_groups, permissions_version())
        groups = all_groups()
    return [groups[group_id] for group_id in group_ids]


def permissions_of(groups: Iterable["Group"]) -> dict[str, bool]:
    """Merges the permissions of ``groups``: a permission is granted when any
    group allows it, unless any group has set it to never. A group without a
    decision counts as the permission's default. The decisions of every group
    are cached as one table, so this never queries per identity.
    """
    stored = _load_group_permissions(permissions_version())
    group_ids = [group.id for group in groups]
    granted: dict[str, bool] = {}
    for key, default in permission_registry.defaults().items():
        levels = [stored.get((group_id, key)) for group_id in group_ids]
        if PermissionLevel.NEVER in levels:
            granted[key] = False
        else:
            granted[key] = any(
                level is PermissionLevel.ALLOW or (level is None and default) for level in levels
            )
    return granted


class HasPermissions:
    """The groups and permissions of an identity, a user or a guest.

    Subclasses provide ``get_groups``; the permissions derive from it and
    from the group permissions table. Groups and their permissions are cached
    whole under the permissions version, so a group change reaches every
    identity at once (see ``invalidate_all_permissions``). Membership is read
    once per request for every loaded user together.
    """

    @property
    def is_authenticated(self) -> bool:
        """Supplied by the flask-login mixin of the subclass."""
        raise NotImplementedError

    @property
    def permissions(self) -> UserPermissions:
        """The effective permissions, read once per request."""
        return permission_manager.for_user(self)

    @property
    def groups(self) -> list["Group"]:
        return self.get_groups()

    @property
    def is_banned(self) -> bool:
        return permission_manager.for_user(self).has_role(GroupRole.BANNED)

    def get_groups(self) -> list["Group"]:
        raise NotImplementedError

    def get_permissions(self) -> dict[str, bool]:
        return permissions_of(self.get_groups())

    def invalidate_cache(self) -> None:
        """Drops what the current request has resolved so far."""
        permission_manager.forget()


@make_comparable
class Group(BaseModel):
    __tablename__: str = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[GroupRole] = mapped_column(
        sa.Enum(
            GroupRole,
            native_enum=False,
            length=20,
            values_callable=lambda roles: [role.value for role in roles],
        ),
        default=GroupRole.MEMBER,
        server_default=GroupRole.MEMBER.value,
        nullable=False,
    )

    # every registered permission the group has decided on; the rest fall
    # back to the permission's default. Loaded on demand: the effective
    # permissions of a user are cached, so loading a group must not drag
    # its rows along.
    permission_rows: Mapped[list["GroupPermission"]] = relationship(cascade="all, delete-orphan")

    @override
    def __repr__(self):
        """Set to a unique key specific to the object in the database.
        Required for cache.memoize() to work across requests.
        """
        return f"<{self.__class__.__name__} {self.id} {self.name}>"

    @property
    def permission_levels(self) -> dict[str, PermissionLevel]:
        """The level of every registered permission. One the group has not
        decided on shows as allow or deny after the permission's default.
        """
        decided = {row.permission: row.level for row in self.permission_rows}
        return {
            key: decided.get(key, PermissionLevel.of(default))
            for key, default in permission_registry.defaults().items()
        }

    @property
    def permissions(self) -> dict[str, bool]:
        """Whether the group on its own grants each registered permission."""
        return {
            key: level is PermissionLevel.ALLOW for key, level in self.permission_levels.items()
        }

    def set_permission(self, key: str, level: PermissionLevel | bool) -> None:
        if isinstance(level, bool):
            level = PermissionLevel.of(level)
        for row in self.permission_rows:
            if row.permission == key:
                row.level = level
                return
        self.permission_rows.append(GroupPermission(permission=key, level=level))

    def set_permissions(self, permissions: Mapping[str, PermissionLevel | bool]) -> None:
        for key, level in permissions.items():
            self.set_permission(key, level)

    @override
    def save(self):
        super().save()
        invalidate_all_permissions()
        return self

    @override
    def delete(self):
        super().delete()
        invalidate_all_permissions()
        return self

    @classmethod
    def selectable_groups_choices(cls):
        return db.session.execute(sa.select(cls.id, cls.name).order_by(cls.name.asc())).all()

    @classmethod
    def get_guest_group(cls) -> "Group":
        return db.session.execute(sa.select(cls).filter(cls.role == GroupRole.GUEST)).scalar_one()

    @classmethod
    def get_member_group(cls) -> "Group":
        """Returns the first member group."""
        return db.session.execute(
            sa.select(cls).filter(cls.role == GroupRole.MEMBER).order_by(cls.id.asc()).limit(1)
        ).scalar_one()


class GroupPermission(BaseModel):
    __tablename__: str = "group_permissions"

    group_id: Mapped[int] = mapped_column(
        sa.ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True
    )
    permission: Mapped[str] = mapped_column(String(255), primary_key=True)
    level: Mapped[PermissionLevel] = mapped_column(
        sa.Enum(
            PermissionLevel,
            native_enum=False,
            length=10,
            values_callable=lambda levels: [level.value for level in levels],
        ),
        nullable=False,
    )


class User(BaseModel, UserMixin, HasPermissions):
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    _password: Mapped[str] = mapped_column("password", String(255), nullable=False)
    date_joined: Mapped[datetime] = mapped_column(
        UTCDateTime(timezone=True), default=time_utcnow, nullable=False
    )
    lastseen: Mapped[datetime | None] = mapped_column(
        UTCDateTime(timezone=True), default=time_utcnow, nullable=True
    )
    birthday: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    website: Mapped[str | None] = mapped_column(String(200), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    signature: Mapped[Text | None] = mapped_column(Text, nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[Text | None] = mapped_column(Text, nullable=True)

    last_failed_login: Mapped[datetime | None] = mapped_column(
        UTCDateTime(timezone=True), nullable=True
    )
    login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    activated: Mapped[bool] = mapped_column(default=False, nullable=False)

    theme: Mapped[str | None] = mapped_column(String(15), nullable=True)
    language: Mapped[str | None] = mapped_column(String(15), default="en", nullable=True)
    open_links_in_new_tab: Mapped[bool | None] = mapped_column(default=None, nullable=True)

    post_count: Mapped[int] = mapped_column(default=0)

    primary_group_id: Mapped[int] = mapped_column(sa.ForeignKey("groups.id"), nullable=False)

    posts: DynamicMapped["Post"] = relationship(
        "Post",
        primaryjoin="User.id == Post.user_id",
        lazy="dynamic",
    )

    topics: DynamicMapped["Topic"] = relationship(
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

    secondary_groups: DynamicMapped[Group] = relationship(
        "Group",
        secondary=groups_users,
        primaryjoin=(groups_users.c.user_id == id),
        lazy="dynamic",
    )

    tracked_topics: WriteOnlyMapped["Topic"] = relationship(
        secondary=topictracker,
        primaryjoin=(topictracker.c.user_id == id),
        passive_deletes=True,
    )

    # Properties
    @property
    @override
    def is_active(self):  # pyright: ignore[reportIncompatibleMethodOverride]
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
            sa.select(Post).filter(Post.user_id == self.id).order_by(Post.date_created.desc())
        ).scalar_one_or_none()

    @property
    def url(self):
        """Returns the url for the user."""
        return url_for("user.profile", username=self.username)

    @property
    def avatar_url(self):
        return url_for("uploads.avatar", avatar=self.avatar)

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
            sa.select(sa.func.count()).select_from(Topic).filter(Topic.user_id == self.id)
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
        return f"<{self.__class__.__name__} {self.username}>"

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
            sa.select(sa.func.count()).select_from(Post).filter_by(user_id=self.id)
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
            sa.select(Topic)
            .where(
                Topic.user_id == self.id,
                Forum.groups.any(Group.id.in_(group_ids)),
            )
            .order_by(Topic.id.desc())
        )
        topics = db.paginate(stmt, page=page, per_page=flaskbb_config["TOPICS_PER_PAGE"])
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
            sa.select(Post)
            .where(
                Post.user_id == self.id,
                Forum.groups.any(Group.id.in_(group_ids)),
            )
            .order_by(Post.id.desc())
        )
        posts = db.paginate(stmt, page=page, per_page=flaskbb_config["TOPICS_PER_PAGE"])
        return posts

    def track_topic(self, topic: "Topic"):
        """Tracks the specified topic.

        :param topic: The topic which should be added to the topic tracker.
        """
        if not self.is_tracking_topic(topic):
            self.tracked_topics.add(topic)
            return self

    def untrack_topic(self, topic: "Topic"):
        """Untracks the specified topic.

        :param topic: The topic which should be removed from the
                      topic tracker.
        """
        if self.is_tracking_topic(topic):
            self.tracked_topics.remove(topic)
            return self

    def is_tracking_topic(self, topic: "Topic"):
        """Checks if the user is already tracking this topic.

        :param topic: The topic which should be checked.
        """
        stmt = self.tracked_topics.select().where(topictracker.c.topic_id == topic.id)
        return db.session.execute(sa.select(stmt.exists())).scalar_one()

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
        stmt = self.secondary_groups.filter(groups_users.c.group_id == group.id)
        return db.session.execute(sa.select(stmt.exists())).scalar_one()

    @override
    def get_groups(self) -> list[Group]:
        secondary_ids = permission_manager.secondary_group_ids(self.id)
        return groups_by_id([self.primary_group_id, *secondary_ids])

    def ban(self):
        """Bans the user. Returns True upon success."""
        if not self.is_banned:
            banned_group = db.session.execute(
                sa.select(Group).filter(Group.role == GroupRole.BANNED)
            ).scalar_one_or_none()

            if not banned_group:
                abort(404)

            self.primary_group = banned_group
            self.save()
            return True
        return False

    def unban(self):
        """Unbans the user. Returns True upon success."""
        if self.is_banned:
            member_group = db.session.scalar(
                sa.select(Group).filter(Group.role == GroupRole.MEMBER).order_by(Group.id.asc())
            )

            if not member_group:
                abort(404)

            self.primary_group = member_group
            self.save()
            return True
        return False

    @override
    def save(self, groups: list[Group] | None = None) -> "User":
        """Saves a user. If groups are provided, they replace the user's
        secondary groups, excluding the primary group.

        :param groups: A list with groups that should be added to the
                       secondary groups from user.
        """
        membership_changed = groups is not None or self._membership_changed()

        if groups is not None:
            with db.session.no_autoflush:
                secondary_groups = set(self.secondary_groups.all())
                selected_groups = set(groups) - {self.primary_group}

                for group in secondary_groups - selected_groups:
                    self.secondary_groups.remove(group)

                for group in selected_groups - secondary_groups:
                    self.secondary_groups.add(group)

        db.session.add(self)
        db.session.commit()
        if membership_changed:
            self.invalidate_cache()
        return self

    def _membership_changed(self) -> bool:
        state = sa.inspect(self)
        return state.persistent and any(
            state.attrs[name].history.has_changes()
            for name in ("primary_group", "primary_group_id", "secondary_groups")
        )

    @override
    def delete(self) -> "User":
        """Deletes the User."""
        db.session.delete(self)
        db.session.commit()

        return self


class Guest(AnonymousUserMixin, HasPermissions):
    @override
    def __repr__(self):
        return "<Guest>"

    @override
    def get_groups(self) -> list[Group]:
        return [group for group in all_groups().values() if group.role is GroupRole.GUEST]
