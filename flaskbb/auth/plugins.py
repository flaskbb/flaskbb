# -*- coding: utf-8 -*-
"""
    flaskbb.auth.plugins
    ~~~~~~~~~~~~~~~~~~~~
    Plugin implementations for FlaskBB auth hooks

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""
from flask import flash
from flask_babelplus import gettext as _
from flask_login import login_user

from . import impl
from ..user.models import User
from ..utils.settings import flaskbb_config
from .services.authentication import (BlockUnactivatedUser, ClearFailedLogins,
                                      DefaultFlaskBBAuthProvider,
                                      MarkFailedLogin)
from .services.factories import account_activator_factory


@impl
def flaskbb_event_user_registered(username):
    user = User.query.filter_by(username=username).first()

    if flaskbb_config["ACTIVATE_ACCOUNT"]:
        service = account_activator_factory()
        service.initiate_account_activation(user.email)
        flash(
            _(
                "An account activation email has been sent to "
                "%(email)s",
                email=user.email
            ), "success"
        )
    else:
        login_user(user)
        flash(_("Thanks for registering."), "success")


@impl(trylast=True)
def flaskbb_authenticate(identifier, secret):
    return DefaultFlaskBBAuthProvider().authenticate(identifier, secret)


@impl(tryfirst=True)
def flaskbb_post_authenticate(user):
    ClearFailedLogins().handle_post_auth(user)
    BlockUnactivatedUser().handle_post_auth(user)


@impl
def flaskbb_authentication_failed(identifier):
    MarkFailedLogin().handle_authentication_failure(identifier)
