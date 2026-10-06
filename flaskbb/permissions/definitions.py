"""
flaskbb.permissions.definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The types a permission is declared with.

:copyright: (c) 2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from dataclasses import dataclass


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
