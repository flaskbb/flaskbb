"""
flaskbb.core.auth.permissions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A per-request snapshot of the data authorization decisions are made from.

:copyright: (c) 2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections.abc import Mapping, Sequence
from functools import cached_property
from typing import Any, Protocol

from flask import g, has_app_context


class ForumLike(Protocol):
    """The members of a forum the requirements read. SQLAlchemy's ``Mapped``
    descriptors do not satisfy typed protocol members, hence ``Any``.
    """

    @property
    def id(self) -> Any: ...

    @property
    def groups(self) -> Any: ...

    @property
    def moderators(self) -> Any: ...


class Identity(Protocol):
    @property
    def is_authenticated(self) -> bool: ...

    def get_permissions(self) -> dict[str, bool]: ...

    def get_groups(self) -> Sequence[Any]: ...


class EffectivePermissions:
    """What the requirements need to know about one identity.

    The groups and permissions live in the cache across requests; reading
    them once per request keeps a page with dozens of permission checks from
    hitting the cache backend for every single one.
    """

    def __init__(self, user: Identity):
        self.user = user
        self.user_id: int | None = getattr(user, "id", None)
        self.is_authenticated = bool(user.is_authenticated)
        self._moderated_forum_ids: dict[int, bool] = {}

    @cached_property
    def granted(self) -> Mapping[str, bool]:
        return self.user.get_permissions()

    @cached_property
    def groups(self) -> Sequence[Any]:
        return self.user.get_groups()

    def has(self, permission: str) -> bool:
        return bool(self.granted.get(permission, False))

    @cached_property
    def group_ids(self) -> frozenset[int]:
        return frozenset(group.id for group in self.groups)

    @cached_property
    def roles(self) -> frozenset[Any]:
        return frozenset(group.role for group in self.groups)

    def has_role(self, role: Any) -> bool:
        return role in self.roles

    @property
    def rank(self) -> int:
        """Ranks the identity by the highest role any of its groups has."""
        return max((role.rank for role in self.roles), default=0)

    def can_access(self, forum: ForumLike) -> bool:
        return any(group.id in self.group_ids for group in forum.groups)

    def moderates(self, forum: ForumLike) -> bool:
        if not self.is_authenticated:
            return False
        if forum.id not in self._moderated_forum_ids:
            self._moderated_forum_ids[forum.id] = any(
                moderator.id == self.user_id for moderator in forum.moderators
            )
        return self._moderated_forum_ids[forum.id]


def permissions_for(user: Identity) -> EffectivePermissions:
    """Returns the snapshot of ``user`` for the current app context, building
    it on first use. Guests share a single snapshot.
    """
    if not has_app_context():
        return EffectivePermissions(user)

    snapshots: dict[Any, EffectivePermissions] = g.setdefault("permissions", {})
    key = getattr(user, "id", None)
    if key not in snapshots:
        snapshots[key] = EffectivePermissions(user)
    return snapshots[key]


def forget_permissions() -> None:
    """Drops the snapshots of the current app context after a permission change."""
    if has_app_context():
        g.pop("permissions", None)
