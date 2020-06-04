# -*- coding: utf-8 -*-
"""
    flaskbb.auth.services.authentication
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Authentication providers, handlers and post-processors
    in FlaskBB

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""
import logging
from datetime import datetime

from pytz import UTC

import attr
from flask_babelplus import gettext as _
from werkzeug.security import check_password_hash

from ...core.auth.authentication import (AuthenticationFailureHandler,
                                         AuthenticationManager,
                                         AuthenticationProvider,
                                         PostAuthenticationHandler,
                                         StopAuthentication)
from ...extensions import db
from ...user.models import User
from ...utils.helpers import time_utcnow

logger = logging.getLogger(__name__)


@attr.s(frozen=True)
class FailedLoginConfiguration(object):
    """
    Used to configure how many failed logins are accepted until an account
    is temporarily locked out and how long to temporarily lock the account
    out for.
    """
    limit = attr.ib()
    lockout_window = attr.ib()


class BlockTooManyFailedLogins(AuthenticationProvider):
    """
    Pre authentication check to block a login from an account that has too
    many failed login attempts in place.
    """

    def __init__(self, configuration):
        self.configuration = configuration

    def authenticate(self, identifier, secret):
        user = User.query.filter(
            db.or_(User.username == identifier, User.email == identifier)
        ).first()

        if user is not None:
            attempts = user.login_attempts
            last_attempt = user.last_failed_login or datetime.min.replace(
                tzinfo=UTC
            )
            reached_attempt_limit = attempts >= self.configuration.limit
            inside_lockout = (
                last_attempt + self.configuration.lockout_window
            ) >= time_utcnow()

            if reached_attempt_limit and inside_lockout:
                raise StopAuthentication(
                    _(
                        "Your account is currently locked out due to too many "
                        "failed login attempts"
                    )
                )


class DefaultFlaskBBAuthProvider(AuthenticationProvider):
    """
    This is the default username/email and password authentication checker,
    locates the user based on the identifer passed -- either username or email
    -- and compares the supplied password to the hash connected to the matching
    user (if any).

    Offers protection against timing attacks that would rely on the difference
    in response time from not matching a password hash.
    """

    def authenticate(self, identifier, secret):
        user = User.query.filter(
            db.or_(User.username == identifier, User.email == identifier)
        ).first()

        if user is not None:
            if check_password_hash(user.password, secret):
                return user
            return None

        check_password_hash("dummy password", secret)
        return None


class MarkFailedLogin(AuthenticationFailureHandler):
    """
    Failure handler that marks the login attempt on the user and sets the
    last failed date when it happened.
    """

    def handle_authentication_failure(self, identifier):
        user = User.query.filter(
            db.or_(User.username == identifier, User.email == identifier)
        ).first()

        if user is not None:
            user.login_attempts += 1
            user.last_failed_login = time_utcnow()


class BlockUnactivatedUser(PostAuthenticationHandler):
    """
    Post auth handler that will block a user that has managed to pass the
    authentication check but has not actually activated their account yet.
    """

    def handle_post_auth(self, user):
        if not user.activated:  # pragma: no branch
            raise StopAuthentication(
                _(
                    "In order to use your account you have to "
                    "activate it through the link we have sent to "
                    "your email address."
                )
            )


class ClearFailedLogins(PostAuthenticationHandler):
    """
    Post auth handler that clears all failed login attempts from a user's
    account.
    """

    def handle_post_auth(self, user):
        user.login_attempts = 0


class PluginAuthenticationManager(AuthenticationManager):
    """
    Authentication manager relying on plugin hooks to manage the authentication
    process. This is the default authentication manager for FlaskBB.
    """

    def __init__(self, plugin_manager, session):
        self.plugin_manager = plugin_manager
        self.session = session

    def authenticate(self, identifier, secret):
        try:
            user = self.plugin_manager.hook.flaskbb_authenticate(
                identifier=identifier, secret=secret
            )
            if user is None:
                raise StopAuthentication(_("Wrong username or password."))
            self.plugin_manager.hook.flaskbb_post_authenticate(user=user)
            return user
        except StopAuthentication:
            self.plugin_manager.hook.flaskbb_authentication_failed(
                identifier=identifier
            )
            raise
        finally:
            try:
                self.session.commit()
            except Exception:
                logger.exception("Exception while processing login")
                self.session.rollback()
                raise
