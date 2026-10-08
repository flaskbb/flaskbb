"""
flaskbb.permissions.manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Owns what a request knows about permissions.

:copyright: (c) 2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections import defaultdict
from typing import Any

import sqlalchemy as sa
from flask import g, has_app_context

from flaskbb.core.auth.permissions import Identity, UserPermissions
from flaskbb.extensions import db


class PermissionManager:
    """Owns the permission state of a request.

    That is one ``UserPermissions`` per identity the request checks, and the
    secondary groups of every user the request has loaded, read in one query
    the first time any of them is needed. Both live on ``g``, so they last
    exactly as long as the request; ``forget`` drops them early after a
    write within the same request.
    """

    PERMISSIONS_KEY = "permissions"
    MEMBERSHIPS_KEY = "group_memberships"

    def for_user(self, user: Identity) -> UserPermissions:
        """The permissions of ``user``, built on first use. Guests share one."""
        if not has_app_context():
            return UserPermissions(user)

        permissions: dict[Any, UserPermissions] = g.setdefault(self.PERMISSIONS_KEY, {})
        key = getattr(user, "id", None)
        if key not in permissions:
            permissions[key] = UserPermissions(user)
        return permissions[key]

    def secondary_group_ids(self, user_id: int) -> tuple[int, ...]:
        """The secondary groups of one user, loaded together with those of
        every other user the request has loaded so far. A page that lists
        many users therefore costs one membership query, not one per user.
        """
        if not has_app_context():
            return self._load_memberships({user_id})[user_id]

        memberships: dict[int, tuple[int, ...]] = g.setdefault(self.MEMBERSHIPS_KEY, {})
        if user_id not in memberships:
            pending = {user_id, *self._loaded_user_ids()} - memberships.keys()
            memberships.update(self._load_memberships(pending))
        return memberships[user_id]

    def forget(self) -> None:
        """Drops everything the request has resolved so far, after a change
        to groups or memberships within the request.
        """
        if has_app_context():
            g.pop(self.PERMISSIONS_KEY, None)
            g.pop(self.MEMBERSHIPS_KEY, None)

    def _loaded_user_ids(self) -> set[int]:
        # imported here because the user models import this package
        from flaskbb.user.models import User

        # the identity key carries the id, so expired instances are not refreshed
        return {key[1][0] for key in db.session.identity_map.keys() if issubclass(key[0], User)}

    def _load_memberships(self, user_ids: set[int]) -> dict[int, tuple[int, ...]]:
        from flaskbb.user.models import groups_users

        found: dict[int, list[int]] = defaultdict(list)
        membership = sa.select(groups_users.c.user_id, groups_users.c.group_id).where(
            groups_users.c.user_id.in_(user_ids)
        )
        for user_id, group_id in db.session.execute(membership):
            found[user_id].append(group_id)
        return {user_id: tuple(found[user_id]) for user_id in user_ids}


permission_manager = PermissionManager()
