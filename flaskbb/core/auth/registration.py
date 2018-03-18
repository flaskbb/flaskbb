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
from ...exceptions import BaseFlaskBBError


@attr.s(hash=True, cmp=False, repr=True, frozen=True)
class UserRegistrationInfo(object):
    username = attr.ib()
    password = attr.ib(repr=False)
    email = attr.ib()
    language = attr.ib()
    group = attr.ib()


class RegistrationError(BaseFlaskBBError):
    pass


class UserRegistrationError(RegistrationError):
    """
    Thrown when a user attempts to register but should
    not be allowed to complete registration.

    If the reason is not tied to a specific attribute then
    the attribute property should be set to None.
    """

    def __init__(self, attribute, reason):
        super(UserRegistrationError, self).__init__(reason)
        self.attribute = attribute
        self.reason = reason


class StopRegistration(RegistrationError):
    def __init__(self, reasons):
        super(StopRegistration, self).__init__()
        self.reasons = reasons


class UserValidator(ABC):
    @abstractmethod
    def validate(self, user_info):
        """
        Used to check if a user should be allowed to register.
        Should raise UserRegistrationError if the user should not be
        allowed to register.
        """
        return True

    def __call__(self, user_info):
        return self.validate(user_info)


class RegistrationService(object):
    def __init__(self, validators, user_repo):
        self.validators = validators
        self.user_repo = user_repo

    def register(self, user_info):
        failures = []

        for v in self.validators:
            try:
                v(user_info)
            except UserRegistrationError as e:
                failures.append((e.attribute, e.reason))

        if failures:
            raise StopRegistration(failures)

        self.user_repo.add(user_info)
