# -*- coding: utf-8 -*-
"""
flaskbb.display.navigation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Helpers to create navigation elements in FlaskBB Templates

:copyright: (c) 2018 the FlaskBB Team
:license: BSD, see LICENSE for more details
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = (
    "NavigationContentType",
    "NavigationLink",
    "NavigationExternalLink",
    "NavigationHeader",
    "NavigationDivider",
)


class NavigationContentType(Enum):
    """
    Content type enum for navigation items.
    """

    link = 0
    external_link = 1
    header = 2
    divider = 3


class NavigationItem:
    """
    Abstract NavigationItem class. Not meant for use but provides the common
    interface for navigation items.
    """

    content_type: NavigationContentType | None = None


@dataclass(eq=True, order=True, repr=True, frozen=True, slots=True)
class NavigationLink(NavigationItem):
    """
    Representation of an internal FlaskBB navigation link::

        NavigationLink(
            endpoint="user.profile",
            name="{}'s Profile".format(user.username),
            icon="fa fa-home",
            active=False,  # default
            urlforkwargs={"username": user.username}
        )
    """

    endpoint: str
    name: str
    icon: str = ""
    active: bool = False
    urlforkwargs: dict[str, Any] = field(default_factory=dict)
    content_type = NavigationContentType.link


@dataclass(eq=True, order=True, repr=True, frozen=True, slots=True)
class NavigationExternalLink(NavigationItem):
    """
    Representation of an external navigation link::

        NavigationExternalLink(
            uri="mailto:{}".format(user.email),
            name="Email {}".format(user.username),
            icon="fa fa-at"
        )
    """

    uri: str
    name: str
    icon: str = ""
    content_type = NavigationContentType.external_link


@dataclass(eq=True, order=True, repr=True, frozen=True, slots=True)
class NavigationHeader(NavigationItem):
    """
    Representation of header text shown in a navigation bar::

        NavigationHeader(
            text="A header",
            icon="fa fa-exclamation"
        )
    """

    text: str
    icon: str = ""
    content_type = NavigationContentType.header


@dataclass(eq=True, order=True, repr=True, frozen=True, slots=True)
class NavigationDivider(NavigationItem):
    """
    Representation of a divider in a navigation bar::

        NavigationDivider()
    """

    content_type = NavigationContentType.divider
