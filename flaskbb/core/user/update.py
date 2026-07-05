# -*- coding: utf-8 -*-
"""
flaskbb.core.user.update
~~~~~~~~~~~~~~~~~~~~~~~~

This modules provides services used in updating user details
across FlaskBB.

:copyright: (c) 2014-2018 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from attrs import asdict, define, field

from flaskbb.user.models import User

from ..changesets import EmptyValue, empty, is_empty


def _should_assign(current: Any, new: Any):
    return not is_empty(new) and current != new


@define(hash=True, eq=True, order=True, repr=True, frozen=True)
class UserDetailsChange(object):
    """
    Object representing a change user details.
    """

    birthday: date | None | EmptyValue = field(default=empty)
    gender: str | None | EmptyValue = field(default=empty)
    location: str | None | EmptyValue = field(default=empty)
    website: str | None | EmptyValue = field(default=empty)
    signature: str | None | EmptyValue = field(default=empty)
    notes: str | None | EmptyValue = field(default=empty)

    def assign_to_user(self, user: User):
        for name, value in asdict(self).items():
            if _should_assign(getattr(user, name), value):
                setattr(user, name, value)


@define(hash=True, eq=True, order=True, repr=False, frozen=True)
class PasswordUpdate(object):
    """
    Object representing an update to a user's password.
    """

    old_password: str = field()
    new_password: str = field()


@define(hash=True, eq=True, order=True, repr=True, frozen=True)
class EmailUpdate(object):
    """
    Object representing a change to a user's email address.
    """

    old_email: str = field(converter=lambda x: x.lower())
    new_email: str = field(converter=lambda x: x.lower())


@define(hash=True, eq=True, order=True, repr=False, frozen=True)
class AvatarUpdate(object):
    """
    Object representing an update to a user's avatar.
    """

    avatar: str = field()


@define(hash=True, eq=True, order=True, repr=True, frozen=True)
class SettingsUpdate(object):
    """
    Object representing an update to a user's settings.
    """

    language: str = field()
    theme: str = field()

    def assign_to_user(self, user: User):
        for name, value in asdict(self).items():
            if _should_assign(getattr(user, name), value):
                setattr(user, name, value)


class UserSettingsUpdatePostProcessor(ABC):
    """
    Used to react to a user updating their settings. This post processor
    recieves the user that updated their settings and the change set that was
    applied to the user. This post processor is called after the update has
    been persisted so further changes must be persisted separately.
    """

    @abstractmethod
    def post_process_settings_update(self, user: User, settings_update):
        """
        This method is abstract
        """
        pass
