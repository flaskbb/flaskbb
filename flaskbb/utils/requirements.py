"""
flaskbb.utils.requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~

Authorization requirements for FlaskBB.

Requirements judge the objects they are given. The policies further down
combine them into one rule per action, shared by the views (which apply them
to the objects of the request, see ``ForRequest``) and the templates (which
apply them to the objects they render, see ``as_template_filter``).

:copyright: (c) 2015 by the FlaskBB Team.
:license: BSD, see LICENSE for more details
"""

import logging
from collections.abc import Callable
from typing import Any, override

from flask_allows2 import And, Or, Permission, Requirement

from flaskbb.exceptions import FlaskBBError
from flaskbb.forum.locals import current_forum, current_post, current_topic
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.permissions import permission_manager
from flaskbb.user.models import GroupRole, User
from flaskbb.utils.helpers import real

logger = logging.getLogger(__name__)


class Has(Requirement):
    def __init__(self, permission: str):
        self.permission = permission

    @override
    def __repr__(self):
        return f"<Has({self.permission!s})>"

    @override
    def fulfill(self, user: User):
        return permission_manager.for_user(user).has(self.permission)


class IsAuthed(Requirement):
    @override
    def fulfill(self, user: User) -> bool:
        return user.is_authenticated


class IsModeratorInForum(IsAuthed):
    def __init__(self, forum: Forum):
        self.forum = forum

    @override
    def __repr__(self):
        return f"<IsModeratorInForum({self.forum!r})>"

    @override
    def fulfill(self, user: User):
        return super().fulfill(user) and permission_manager.for_user(user).moderates(self.forum)


class IsMorePrivilegedThan(Requirement):
    """Fulfilled when the acting user outranks ``target``.

    The comparison is strict, so it is never fulfilled for an equally
    privileged target - including the acting user themselves.
    """

    def __init__(self, target: User):
        self.target = target

    @override
    def __repr__(self):
        return f"<IsMorePrivilegedThan({self.target!s})>"

    @override
    def fulfill(self, user: User):
        acting, target = permission_manager.for_user(user), permission_manager.for_user(self.target)
        return acting.rank > target.rank


class IsSelf(Requirement):
    """Fulfilled when the acting user *is* ``target``."""

    def __init__(self, target: User):
        self.target = target

    @override
    def __repr__(self):
        return f"<IsSelf({self.target!s})>"

    @override
    def fulfill(self, user: User):
        return user.id == self.target.id


class IsSameUser(IsAuthed):
    """Fulfilled when the acting user wrote ``content``, a topic or a post."""

    def __init__(self, content: Topic | Post):
        self.content = content

    @override
    def __repr__(self):
        return f"<IsSameUser({self.content!r})>"

    @override
    def fulfill(self, user: User):
        return super().fulfill(user) and user.id == self.content.user_id


class TopicNotLocked(Requirement):
    def __init__(self, topic: Topic):
        self.topic = topic

    @override
    def __repr__(self):
        return f"<TopicNotLocked({self.topic!r})>"

    @override
    def fulfill(self, user: User):
        return not (self.topic.locked or self.topic.forum.locked)


class ForumNotLocked(Requirement):
    def __init__(self, forum: Forum):
        self.forum = forum

    @override
    def __repr__(self):
        return f"<ForumNotLocked({self.forum!r})>"

    @override
    def fulfill(self, user: User):
        return not self.forum.locked


class CanAccessForum(Requirement):
    def __init__(self, forum: Forum):
        self.forum = forum

    @override
    def __repr__(self):
        return f"<CanAccessForum({self.forum!r})>"

    @override
    def fulfill(self, user: User):
        return permission_manager.for_user(user).can_access(self.forum)


class IsAtLeast(Requirement):
    """Fulfilled when a group of the acting user has ``role`` or outranks it."""

    def __init__(self, role: GroupRole):
        self.role = role

    @override
    def __repr__(self):
        return f"<IsAtLeast({self.role!s})>"

    @override
    def fulfill(self, user: User):
        return permission_manager.for_user(user).rank >= self.role.rank


IsAdmin = IsAtLeast(GroupRole.ADMINISTRATOR)

IsAtleastSuperModerator = IsAtLeast(GroupRole.SUPER_MODERATOR)

IsAtleastModerator = IsAtLeast(GroupRole.MODERATOR)

CanBanUser = Or(IsAtleastSuperModerator, Has("mod_banuser"))

CanEditUser = Or(IsAtleastSuperModerator, Has("mod_edituser"))


# Policies: one rule per action.


def can_access_forum(forum: Forum) -> Requirement:
    return CanAccessForum(forum)


def can_moderate(forum: Forum) -> Requirement:
    return Or(IsAtleastSuperModerator, IsModeratorInForum(forum))


def can_post_topic(forum: Forum) -> Requirement:
    return Or(
        IsAdmin,
        And(
            ForumNotLocked(forum),
            Or(And(CanAccessForum(forum), Has("posttopic")), can_moderate(forum)),
        ),
    )


def can_post_reply(topic: Topic) -> Requirement:
    return Or(
        can_moderate(topic.forum),
        And(CanAccessForum(topic.forum), Has("postreply"), TopicNotLocked(topic)),
    )


def can_post_attachment(forum: Forum) -> Requirement:
    return Or(And(IsAuthed(), Has("postattachment")), can_moderate(forum))


def _can_edit(topic: Topic, content: Topic | Post) -> Requirement:
    forum = topic.forum
    return Or(
        IsAtleastSuperModerator,
        And(IsModeratorInForum(forum), Has("editpost")),
        And(CanAccessForum(forum), IsSameUser(content), Has("editpost"), TopicNotLocked(topic)),
    )


def can_edit_post(post: Post) -> Requirement:
    return _can_edit(post.topic, post)


can_delete_post = can_edit_post


def can_edit_topic(topic: Topic) -> Requirement:
    return And(
        Or(can_post_topic(topic.forum), can_moderate(topic.forum)),
        _can_edit(topic, topic),
    )


def can_delete_topic(topic: Topic) -> Requirement:
    forum = topic.forum
    return Or(
        IsAtleastSuperModerator,
        And(IsModeratorInForum(forum), Has("deletetopic")),
        And(CanAccessForum(forum), IsSameUser(topic), Has("deletetopic"), TopicNotLocked(topic)),
    )


def can_edit_user(target: User | None = None) -> Requirement:
    """``CanEditUser``, restricted to targets the acting user outranks.

    Administrators are exempt from the ranking check so that they can still
    manage each other. Everyone who may edit users at all may reach their own
    account - which fields they actually get is decided by the form, so this
    does not let anyone raise their own privileges.
    """
    if target is None:
        return CanEditUser
    return And(CanEditUser, Or(IsAdmin, IsSelf(target), IsMorePrivilegedThan(target)))


def can_ban_user(target: User | None = None) -> Requirement:
    """``CanBanUser``, restricted to targets the acting user outranks.

    Administrators are exempt from the ranking check so that they can still
    manage each other.
    """
    if target is None:
        return CanBanUser
    return And(CanBanUser, Or(IsAdmin, IsMorePrivilegedThan(target)))


# Views


def request_forum() -> Forum:
    forum = real(current_forum)
    if forum is None:
        raise FlaskBBError("Could not load forum data")
    return forum


def request_topic() -> Topic:
    topic = real(current_topic)
    if topic is None:
        raise FlaskBBError("Could not load topic data")
    return topic


def request_post() -> Post:
    post = real(current_post)
    if post is None:
        raise FlaskBBError("Could not load post data")
    return post


class ForRequest[T](Requirement):
    """Applies ``policy`` to the object ``load`` reads from the request.

    View decorators are built at import time, before the forum, topic or
    post of a request exists, so the policy is applied on every evaluation.
    """

    def __init__(self, policy: Callable[[T], Requirement], load: Callable[[], T]):
        self.policy = policy
        self.load = load

    @override
    def __repr__(self):
        return f"<ForRequest({self.policy.__name__}, {self.load.__name__})>"

    @override
    def fulfill(self, user: User):
        return self.policy(self.load())(user)


# Templates


def permission_with_identity(requirement: Requirement, name: str | None = None):
    """
    Permission instance factory that can set a user at construction time
    can optionally name the closure for nicer debugging
    """

    def _(user: User):
        return Permission(requirement, identity=user)

    if name is not None:
        _.__name__ = name

    return _


def as_template_filter(policy: Callable[..., Requirement], name: str):
    """Turns a policy into a Jinja filter: ``current_user|name(obj)``."""

    def _(user: User, *args: Any):
        return Permission(policy(*args), identity=user)

    _.__name__ = name
    return _
