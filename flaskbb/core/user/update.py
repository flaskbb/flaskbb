# -*- coding: utf-8 -*-
"""
    flaskbb.core.user.update
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This modules provides services used in updating user details
    across FlaskBB.

    :copyright: (c) 2014-2018 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""

from abc import abstractmethod

import attr

from ..._compat import ABC
from ..changesets import empty, is_empty


def _should_assign(current, new):
    return not is_empty(new) and current != new


@attr.s(hash=True, cmp=True, repr=True, frozen=True)
class UserDetailsChange(object):
    """
    Object representing a change user details.
    """

    birthday = attr.ib(default=empty)
    gender = attr.ib(default=empty)
    location = attr.ib(default=empty)
    website = attr.ib(default=empty)
    avatar = attr.ib(default=empty)
    signature = attr.ib(default=empty)
    notes = attr.ib(default=empty)

    def assign_to_user(self, user):
        for (name, value) in attr.asdict(self).items():
            if _should_assign(getattr(user, name), value):
                setattr(user, name, value)


@attr.s(hash=True, cmp=True, repr=False, frozen=True)
class PasswordUpdate(object):
    """
    Object representing an update to a user's password.
    """

    old_password = attr.ib()
    new_password = attr.ib()


@attr.s(hash=True, cmp=True, repr=True, frozen=True)
class EmailUpdate(object):
    """
    Object representing a change to a user's email address.
    """

    # TODO(anr): Change to str.lower once Python2 is dropped
    old_email = attr.ib(converter=lambda x: x.lower())
    new_email = attr.ib(converter=lambda x: x.lower())


@attr.s(hash=True, cmp=True, repr=True, frozen=True)
class SettingsUpdate(object):
    """
    Object representing an update to a user's settings.
    """

    language = attr.ib()
    theme = attr.ib()

    def assign_to_user(self, user):
        for (name, value) in attr.asdict(self).items():
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
    def post_process_settings_update(self, user, settings_update):
        """
        This method is abstract
        """
        pass
