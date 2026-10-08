"""
flaskbb.core.auth.permissions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The resolved permissions of one identity, as the requirements read them.

:copyright: (c) 2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections.abc import Iterator, Mapping, Sequence
from functools import cached_property
from typing import Any, override, Protocol


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


class UserPermissions(Mapping[str, bool]):
    """The resolved permissions of one identity, a user or a guest.

    A mapping of permission key to whether the identity has it, plus the
    groups and roles the requirements compare. Everything is read on first
    use and kept for the rest of the request, so a page with dozens of
    permission checks resolves each identity once.
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

    @override
    def __getitem__(self, permission: str) -> bool:
        return self.granted[permission]

    @override
    def __iter__(self) -> Iterator[str]:
        return iter(self.granted)

    @override
    def __len__(self) -> int:
        return len(self.granted)

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
