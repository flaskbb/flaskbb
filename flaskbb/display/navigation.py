# -*- coding: utf-8 -*-
"""
    flaskbb.display.navigation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Helpers to create navigation elements in FlaskBB Templates

    :copyright: (c) 2018 the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""

from abc import abstractproperty
from enum import Enum

import attr

from .._compat import ABC

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


class NavigationItem(ABC):
    """
    Abstract NavigationItem class. Not meant for use but provides the common
    interface for navigation items.
    """
    content_type = abstractproperty(lambda: None)


@attr.s(cmp=True, hash=True, repr=True, frozen=True, slots=True)
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

    endpoint = attr.ib()
    name = attr.ib()
    icon = attr.ib(default="")
    active = attr.ib(default=False)
    urlforkwargs = attr.ib(factory=dict)
    content_type = NavigationContentType.link


@attr.s(cmp=True, hash=True, repr=True, frozen=True, slots=True)
class NavigationExternalLink(NavigationItem):
    """
    Representation of an external navigation link::

        NavigationExternalLink(
            uri="mailto:{}".format(user.email),
            name="Email {}".format(user.username),
            icon="fa fa-at"
        )
    """
    uri = attr.ib()
    name = attr.ib()
    icon = attr.ib(default="")
    content_type = NavigationContentType.external_link


@attr.s(cmp=True, hash=True, repr=True, frozen=True, slots=True)
class NavigationHeader(NavigationItem):
    """
    Representation of header text shown in a navigation bar::

        NavigationHeader(
            text="A header",
            icon="fa fa-exclamation"
        )
    """

    text = attr.ib()
    icon = attr.ib(default="")
    content_type = NavigationContentType.header


@attr.s(cmp=False, hash=True, repr=True, frozen=True, slots=True)
class NavigationDivider(NavigationItem):
    """
    Representation of a divider in a navigation bar::

        NavigationDivider()
    """

    content_type = NavigationContentType.divider
