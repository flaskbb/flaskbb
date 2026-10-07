"""
flaskbb.permissions.definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The types a permission is declared with.

:copyright: (c) 2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import enum
from dataclasses import dataclass


class PermissionLevel(enum.StrEnum):
    """What a group has decided about one permission.

    A member has a permission when any of their groups allows it, unless
    one of their groups has set it to never.
    """

    ALLOW = "allow"
    DENY = "deny"
    NEVER = "never"

    @classmethod
    def of(cls, granted: bool) -> "PermissionLevel":
        return cls.ALLOW if granted else cls.DENY


@dataclass(frozen=True)
class PermissionDefinition:
    key: str  # lower_snake_case, unique within its group
    name: str
    description: str
    default: bool = False  # what a group without a stored decision gets


@dataclass(frozen=True)
class PermissionGroup:
    """A set of related permissions, shown as one section of the group form.

    A plugin's group ``key`` must equal the plugin's name: its permissions
    are stored prefixed with that key, so they can't collide with FlaskBB's
    own or with another plugin's.
    """

    key: str
    name: str
    permissions: tuple[PermissionDefinition, ...]
