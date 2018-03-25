# -*- coding: utf-8 -*-
"""
    flaskbb.auth.services.factories
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Factory functions for various FlaskBB auth services

    :copyright: 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""
from datetime import timedelta

from flask import current_app

from ...extensions import db
from ...tokens import FlaskBBTokenSerializer
from ...tokens.verifiers import EmailMatchesUserToken
from ...user.models import User
from ...user.repo import UserRepository
from ...utils.settings import flaskbb_config
from .activation import AccountActivator
from .password import ResetPasswordService
from .registration import (EmailUniquenessValidator, RegistrationService,
                           UsernameRequirements, UsernameUniquenessValidator,
                           UsernameValidator)


def registration_service_factory():
    blacklist = [
        w.strip()
        for w in flaskbb_config["AUTH_USERNAME_BLACKLIST"].split(",")
    ]

    requirements = UsernameRequirements(
        min=flaskbb_config["AUTH_USERNAME_MIN_LENGTH"],
        max=flaskbb_config["AUTH_USERNAME_MAX_LENGTH"],
        blacklist=blacklist
    )

    validators = [
        EmailUniquenessValidator(User),
        UsernameUniquenessValidator(User),
        UsernameValidator(requirements)
    ]

    return RegistrationService(validators, UserRepository(db))


def reset_service_factory():
    token_serializer = FlaskBBTokenSerializer(
        current_app.config['SECRET_KEY'], expiry=timedelta(hours=1)
    )
    verifiers = [EmailMatchesUserToken(User)]
    return ResetPasswordService(
        token_serializer, User, token_verifiers=verifiers
    )


def account_activator_factory():
    token_serializer = FlaskBBTokenSerializer(
        current_app.config['SECRET_KEY'], expiry=timedelta(hours=1)
    )
    return AccountActivator(token_serializer, User)
