# -*- coding: utf-8 -*-
"""
    flaskbb.permissions.utils
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Helpers for dealing with permissions in FlaskBB

    :copyright: 2017, the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""

from itertools import chain, groupby

from werkzeug.datastructures import ImmutableDict

from flaskbb._compat import Mapping


# Use: This can be created once at request start up
# and then consulted when needed, doing the heavy lifting
# only when asked and then caching the result so it doesn't
# have to do it again as merge_permissions is potentially
# expensive to call as it does a *lot* of iteration

# Preferably, this would be on some thread local object
# so it can be intelligently cached rather than potentially
# running afoul of other users
class PermissionManager(Mapping):
    """
    Acts as a mapping to permissions and determines
    the best combination of permissions for a user
    in the given context
    """

    def __init__(self, all_permissions, user, category=None, forum=None):
        self._all_permissions = all_permissions
        self._user = user
        self._category = category
        self._forum = forum
        self._combined = None

    @property
    def permissions(self):
        if not self._combined:
            self._combined = self._combine_permissions()
        return self._combined

    def _combine_permissions(self):
        return ImmutableDict(merge_permissions(
            all_permission=self._all_permissions,
            user=self._user,
            category=self._category,
            forum=self._forum
        ))

    def __getitem__(self, name):
        try:
            return self.permissions[name]
        except KeyError:
            return False

    def __iter__(self):
        return iter(self.permissions)

    def __len__(self):
        return len(self.permissions)


def merge_permissions(all_permissions, user, category=None, forum=None):
    """
    Combines user, group, category and forum permissions
    with the defaults all permissions to determine a user's
    current permissions in the current context.

    If a user is an adminstrator, super moderator or moderator
    in the current context, then their personal permissions
    will take priority over the local context's permissions.

    Otherwise, the local context's permissions will take
    priority over the user's permissions.
    """
    permissions = {}
    permissions.update(dict((p.name, p.default) for p in all_permissions))

    if _user_perms_have_priority(user, forum):
        permissions.update(
            _find_best_combo(
                merge_user_permissions(user), merge_forum_permissions(category, forum)
            )
        )
    else:
        permissions.update(merge_user_permissions(user))
        permissions.update(merge_forum_permissions(category, forum))

    return permissions


def merge_user_permissions(user):
    """
    Merges all permissions a user might have into an easy to use dictionary
    """
    permissions = {}
    permissions.update(_groups_permissions(user.groups))
    permissions.update(dict((p.permission.name, p.value) for p in user.permissions_))
    return permissions


def merge_forum_permissions(all_permissions, category=None, forum=None):
    permissions = {}

    if category:
        permissions.update((p.permission.name, p.value) for p in category.permissions_)

    if forum:
        permissions.update((p.permission.name, p.value) for p in forum.permissions_)

    return permissions


def _groups_permissions(groups):
    return {
        name: any(v[1] for v in values)
        for name, values in groupby(
            chain.from_iterable(
                map(lambda p: (p.permission.name, p.value), g.permissions_) for g in groups
            ), lambda p: p[0]
        )
    }


def _user_perms_have_priority(user, forum=None):
    return (
        (user.level in {'admin', 'super_mod'})
        or forum and user.level == 'mod' and user in forum.moderators
    )


def _find_best_combo(user_permissions, forum_permissions):
    """
    Finds the combination that results in the most permissions
    for a user in the current context
    """
    permissions = {}
    user_owned_perms = set(user_permissions.keys())
    forum_owned_perms = set(forum_permissions.keys())
    common = user_owned_perms & forum_owned_perms

    if not common:
        permissions.update(user_permissions)
        permissions.update(forum_permissions)

    else:
        for perm in common:
            permissions[perm] = user_permissions[perm] or forum_owned_perms[perm]

        for perm in (user_owned_perms - common):
            permissions[perm] = user_permissions[perm]

        for perm in (forum_owned_perms - common):
            permissions[perm] = forum_permissions[perm]

    return permissions
