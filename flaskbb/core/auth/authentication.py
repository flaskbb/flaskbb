# -*- coding: utf-8 -*-
"""
    flaskbb.core.auth.authentication
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    :copyright: (c) 2014-2018 the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""

from abc import abstractmethod

from ..._compat import ABC
from ..exceptions import BaseFlaskBBError


class StopAuthentication(BaseFlaskBBError):
    """
    Used by Authentication providers to halt any further
    attempts to authenticate a user.
    """

    def __init__(self, reason):
        super(StopAuthentication, self).__init__(reason)
        self.reason = reason


class ForceLogout(BaseFlaskBBError):
    """
    Used to forcefully log a user out.
    """

    def __init__(self, reason):
        super(ForceLogout, self).__init__(reason)
        self.reason = reason


class AuthenticationManager(ABC):

    @abstractmethod
    def authenticate(self, identifier, secret):
        """
        Manages the entire authentication process in FlaskBB.

        If a user is successfully authenticated, it is returned
        from this method.
        """
        pass


class AuthenticationProvider(ABC):

    @abstractmethod
    def authenticate(self, identifier, secret):
        pass

    def __call__(self, identifier, secret):
        return self.authenticate(identifier, secret)


class AuthenticationFailureHandler(ABC):

    @abstractmethod
    def handle_authentication_failure(self, identifier):
        pass

    def __call__(self, identifier):
        self.handle_authentication_failure(identifier)


class PostAuthenticationHandler(ABC):

    @abstractmethod
    def handle_post_auth(self, user):
        pass

    def __call__(self, user):
        self.handle_post_auth(user)


class ReauthenticateManager(ABC):

    @abstractmethod
    def reauthenticate(self, user, secret):
        pass

    def __call__(self, user, secret):
        pass


class ReauthenticateProvider(ABC):

    @abstractmethod
    def reauthenticate(self, user, secret):
        pass

    def __call__(self, user, secret):
        self.handle_reauth(user, secret)


class ReauthenticateFailureHandler(ABC):

    @abstractmethod
    def handle_reauth_failure(self, user):
        pass

    def __call__(self, user):
        self.handle_reauth_failure(user)


class PostReauthenticateHandler(ABC):

    @abstractmethod
    def handle_post_reauth(self, user):
        pass

    def __call__(self, user):
        self.handle_post_reauth(user)
