#  -*- coding: utf-8 -*-
"""
    flaskbb.auth.services
    ~~~~~~~~~~~~~~~~~~~~~

    Implementation of services found in flaskbb.core.auth.services

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

from collections import namedtuple

from sqlalchemy import func

from ...core.auth.registration import UserRegistrationError, UserValidator
from ...core.tokens import TokenVerifier, TokenVerificationError

__all__ = ("UsernameRequirements", "UsernameValidator",
           "EmailUniquenessValidator", "UsernameUniquenessValidator")

UsernameRequirements = namedtuple(
    'UsernameRequirements', ['min', 'max', 'blacklist']
)


class UsernameValidator(UserValidator):

    def __init__(self, requirements):
        self._requirements = requirements

    def validate(self, user_info):
        if not (self._requirements.min <= len(user_info.username) <=
                self._requirements.max):
            raise UserRegistrationError(
                'username',
                'Username must be between {} and {} characters long'.format(
                    self._requirements.min, self._requirements.max
                )
            )

        if user_info.username in self._requirements.blacklist:  # pragma: no branch
            raise UserRegistrationError(
                'username',
                '{} is a forbidden username'.format(user_info.username)
            )


class UsernameUniquenessValidator(UserValidator):

    def __init__(self, users):
        self.users = users

    def validate(self, user_info):
        count = self.users.query.filter(
            func.lower(self.users.username) == user_info.username
        ).count()
        if count != 0:  # pragma: no branch
            raise UserRegistrationError(
                'username',
                '{} is already registered'.format(user_info.username)
            )


class EmailUniquenessValidator(UserValidator):

    def __init__(self, users):
        self.users = users

    def validate(self, user_info):
        count = self.users.query.filter(
            func.lower(self.users.email) == user_info.email
        ).count()
        if count != 0:  # pragma: no branch
            raise UserRegistrationError(
                'email', '{} is already registered'.format(user_info.email)
            )
