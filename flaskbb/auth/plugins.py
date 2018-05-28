# -*- coding: utf-8 -*-
"""
    flaskbb.auth.plugins
    ~~~~~~~~~~~~~~~~~~~~
    Plugin implementations for FlaskBB auth hooks

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""
from flask import flash, redirect, url_for
from flask_login import current_user, logout_user

from . import impl
from ..core.auth.authentication import ForceLogout
from ..extensions import db
from ..user.models import User
from ..utils.settings import flaskbb_config
from .services.authentication import (
    BlockUnactivatedUser,
    ClearFailedLogins,
    DefaultFlaskBBAuthProvider,
    MarkFailedLogin,
)
from .services.factories import account_activator_factory
from .services.reauthentication import (
    ClearFailedLoginsOnReauth,
    DefaultFlaskBBReauthProvider,
    MarkFailedReauth,
)
from .services.registration import (
    AutoActivateUserPostProcessor,
    AutologinPostProcessor,
    EmailUniquenessValidator,
    SendActivationPostProcessor,
    UsernameRequirements,
    UsernameUniquenessValidator,
    UsernameValidator,
)


@impl(trylast=True)
def flaskbb_authenticate(identifier, secret):
    return DefaultFlaskBBAuthProvider().authenticate(identifier, secret)


@impl(tryfirst=True)
def flaskbb_post_authenticate(user):
    handlers = [ClearFailedLogins()]

    if flaskbb_config["ACTIVATE_ACCOUNT"]:
        handlers.append(BlockUnactivatedUser())

    for handler in handlers:
        handler.handle_post_auth(user)


@impl
def flaskbb_authentication_failed(identifier):
    MarkFailedLogin().handle_authentication_failure(identifier)


@impl(trylast=True)
def flaskbb_reauth_attempt(user, secret):
    return DefaultFlaskBBReauthProvider().reauthenticate(user, secret)


@impl
def flaskbb_reauth_failed(user):
    MarkFailedReauth().handle_reauth_failure(user)


@impl
def flaskbb_post_reauth(user):
    ClearFailedLoginsOnReauth().handle_post_reauth(user)


@impl
def flaskbb_errorhandlers(app):

    @app.errorhandler(ForceLogout)
    def handle_force_logout(error):
        if current_user:
            logout_user()
            if error.reason:
                flash(error.reason, "danger")
        return redirect(url_for("forum.index"))


@impl
def flaskbb_gather_registration_validators():
    blacklist = [
        w.strip() for w in flaskbb_config["AUTH_USERNAME_BLACKLIST"].split(",")
    ]

    requirements = UsernameRequirements(
        min=flaskbb_config["AUTH_USERNAME_MIN_LENGTH"],
        max=flaskbb_config["AUTH_USERNAME_MAX_LENGTH"],
        blacklist=blacklist,
    )

    return [
        EmailUniquenessValidator(User),
        UsernameUniquenessValidator(User),
        UsernameValidator(requirements),
    ]


@impl
def flaskbb_registration_post_processor(user):
    handlers = []

    if flaskbb_config["ACTIVATE_ACCOUNT"]:
        handlers.append(
            SendActivationPostProcessor(account_activator_factory())
        )
    else:
        handlers.append(AutologinPostProcessor())
        handlers.append(AutoActivateUserPostProcessor(db, flaskbb_config))

    for handler in handlers:
        handler.post_process(user)
