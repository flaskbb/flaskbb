#  -*- coding: utf-8 -*-
"""
    flaskbb.auth.services
    ~~~~~~~~~~~~~~~~~~~~~

    Implementation of services found in flaskbb.core.auth.services

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

import attr
from flask_babelplus import gettext as _
from sqlalchemy import func

from ...core.auth.registration import UserRegistrationService, UserValidator
from ...core.exceptions import StopValidation, ValidationError

__all__ = (
    "UsernameRequirements", "UsernameValidator", "EmailUniquenessValidator",
    "UsernameUniquenessValidator"
)


@attr.s(hash=False, repr=True, frozen=True, cmp=False)
class UsernameRequirements(object):
    """
    Configuration for username requirements, minimum and maximum length
    and disallowed names.
    """
    min = attr.ib()
    max = attr.ib()
    blacklist = attr.ib()


class UsernameValidator(UserValidator):
    """
    Validates that the username for the registering user meets the minimum
    requirements (appropriate length, not a forbidden name).
    """

    def __init__(self, requirements):
        self._requirements = requirements

    def validate(self, user_info):
        if not (self._requirements.min <= len(user_info.username) <=
                self._requirements.max):
            raise ValidationError(
                'username',
                _(
                    'Username must be between %(min)s and %(max)s characters long',  # noqa
                    min=self._requirements.min,
                    max=self._requirements.max
                )
            )

        is_blacklisted = user_info.username in self._requirements.blacklist
        if is_blacklisted:  # pragma: no branch
            raise ValidationError(
                'username',
                _(
                    '%(username)s is a forbidden username',
                    username=user_info.username
                )
            )


class UsernameUniquenessValidator(UserValidator):
    """
    Validates that the provided username is unique in the application.
    """

    def __init__(self, users):
        self.users = users

    def validate(self, user_info):
        count = self.users.query.filter(
            func.lower(self.users.username) == user_info.username
        ).count()
        if count != 0:  # pragma: no branch
            raise ValidationError(
                'username',
                _(
                    '%(username)s is already registered',
                    username=user_info.username
                )
            )


class EmailUniquenessValidator(UserValidator):
    """
    Validates that the provided email is unique in the application.
    """

    def __init__(self, users):
        self.users = users

    def validate(self, user_info):
        count = self.users.query.filter(
            func.lower(self.users.email) == user_info.email
        ).count()
        if count != 0:  # pragma: no branch
            raise ValidationError(
                'email',
                _('%(email)s is already registered', email=user_info.email)
            )


class RegistrationService(UserRegistrationService):
    """
    Default registration service for FlaskBB, runs the registration information
    against the provided validators and if it passes, creates the user.

    If any of the provided
    :class:`UserValidators<flaskbb.core.auth.registration.UserValidator>`
    raise a :class:`ValidationError<flaskbb.core.exceptions.ValidationError>`
    then the register method will raise a
    :class:`StopValidation<flaskbb.core.exceptions.StopValidation>` with all
    reasons why the registration was prevented.
    """

    def __init__(self, validators, user_repo):
        self.validators = validators
        self.user_repo = user_repo

    def register(self, user_info):
        failures = []

        for v in self.validators:
            try:
                v(user_info)
            except ValidationError as e:
                failures.append((e.attribute, e.reason))
        if failures:
            raise StopValidation(failures)
        self.user_repo.add(user_info)
