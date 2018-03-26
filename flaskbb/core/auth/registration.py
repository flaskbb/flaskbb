# -*- coding: utf-8 -*-
"""
    flaskbb.core.auth.services
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    This modules provides services used in authentication and authorization
    across FlaskBB.

    :copyright: (c) 2014-2018 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""

from abc import abstractmethod

import attr

from ..._compat import ABC


@attr.s(hash=True, cmp=False, repr=True, frozen=True)
class UserRegistrationInfo(object):
    username = attr.ib()
    password = attr.ib(repr=False)
    email = attr.ib()
    language = attr.ib()
    group = attr.ib()


class UserValidator(ABC):
    @abstractmethod
    def validate(self, user_info):
        """
        Used to check if a user should be allowed to register.
        Should raise ValidationError if the user should not be
        allowed to register.
        """
        return True

    def __call__(self, user_info):
        return self.validate(user_info)


class UserRegistrationService(ABC):
    @abstractmethod
    def register(self, user_info):
        pass
