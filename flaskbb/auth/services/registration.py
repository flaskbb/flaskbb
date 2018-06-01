#  -*- coding: utf-8 -*-
"""
    flaskbb.auth.services
    ~~~~~~~~~~~~~~~~~~~~~

    Implementation of services found in flaskbb.core.auth.services

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

from datetime import datetime
from itertools import chain

import attr
from flask import flash
from flask_babelplus import gettext as _
from flask_login import login_user
from pytz import UTC
from sqlalchemy import func

from ...core.auth.registration import (
    RegistrationPostProcessor,
    UserRegistrationService,
    UserValidator,
)
from ...core.exceptions import (
    PersistenceError,
    StopValidation,
    ValidationError,
)
from ...user.models import User

__all__ = (
    "AutoActivateUserPostProcessor",
    "AutologinPostProcessor",
    "EmailUniquenessValidator",
    "RegistrationService",
    "SendActivationPostProcessor",
    "UsernameRequirements",
    "UsernameUniquenessValidator",
    "UsernameValidator",
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
        if not (
            self._requirements.min
            <= len(user_info.username)
            <= self._requirements.max
        ):
            raise ValidationError(
                "username",
                _(
                    "Username must be between %(min)s and %(max)s characters long",  # noqa
                    min=self._requirements.min,
                    max=self._requirements.max,
                ),
            )

        is_blacklisted = user_info.username in self._requirements.blacklist
        if is_blacklisted:  # pragma: no branch
            raise ValidationError(
                "username",
                _(
                    "%(username)s is a forbidden username",
                    username=user_info.username,
                ),
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
                "username",
                _(
                    "%(username)s is already registered",
                    username=user_info.username,
                ),
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
                "email",
                _("%(email)s is already registered", email=user_info.email),
            )


class SendActivationPostProcessor(RegistrationPostProcessor):
    """
    Sends an activation request after registration

    :param account_activator:
    :type account_activator: :class:`~flaskbb.core.auth.activation.AccountActivator`
    """  # noqa

    def __init__(self, account_activator):
        self.account_activator = account_activator

    def post_process(self, user):
        self.account_activator.initiate_account_activation(user.email)
        flash(
            _(
                "An account activation email has been sent to %(email)s",
                email=user.email,
            ),
            "success",
        )


class AutologinPostProcessor(RegistrationPostProcessor):
    """
    Automatically logs a user in after registration
    """

    def post_process(self, user):
        login_user(user)
        flash(_("Thanks for registering."), "success")


class AutoActivateUserPostProcessor(RegistrationPostProcessor):
    """
    Automatically marks the user as activated if activation isn't required
    for the forum.

    :param db: Configured Flask-SQLAlchemy extension object
    :param config: Current flaskbb configuration object
    """

    def __init__(self, db, config):
        self.db = db
        self.config = config

    def post_process(self, user):
        if not self.config['ACTIVATE_ACCOUNT']:
            user.activated = True
            self.db.session.commit()


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

    def __init__(self, plugins, users, db):
        self.plugins = plugins
        self.users = users
        self.db = db

    def register(self, user_info):
        try:
            self._validate_registration(user_info)
        except StopValidation as e:
            self._handle_failure(user_info, e.reasons)
            raise

        user = self._store_user(user_info)
        self._post_process(user)
        return user

    def _validate_registration(self, user_info):
        failures = []
        validators = self.plugins.hook.flaskbb_gather_registration_validators()

        for v in chain.from_iterable(validators):
            try:
                v(user_info)
            except ValidationError as e:
                failures.append((e.attribute, e.reason))
        if failures:
            raise StopValidation(failures)

    def _handle_failure(self, user_info, failures):
        self.plugins.hook.flaskbb_registration_failure_handler(
            user_info=user_info, failures=failures
        )

    def _store_user(self, user_info):
        try:
            user = User(
                username=user_info.username,
                email=user_info.email,
                password=user_info.password,
                language=user_info.language,
                primary_group_id=user_info.group,
                date_joined=datetime.now(UTC),
            )
            self.db.session.add(user)
            self.db.session.commit()
            return user
        except Exception:
            self.db.session.rollback()
            raise PersistenceError("Could not persist user")

    def _post_process(self, user):
        self.plugins.hook.flaskbb_registration_post_processor(user=user)
