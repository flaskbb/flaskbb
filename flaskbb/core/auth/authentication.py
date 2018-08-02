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

    :param reason str: The reason why authentication was halted
    """

    def __init__(self, reason):
        super(StopAuthentication, self).__init__(reason)
        self.reason = reason


class ForceLogout(BaseFlaskBBError):
    """
    Used to forcefully log a user out.

    :param reason str: The reason why the user was force logged out
    """

    def __init__(self, reason):
        super(ForceLogout, self).__init__(reason)
        self.reason = reason


class AuthenticationManager(ABC):
    """
    Used to handle the authentication process. A default is implemented,
    however this interface is provided in case alternative flows are needed.

    If a user successfully passes through the entire authentication process,
    then it should be returned to the caller.
    """

    @abstractmethod
    def authenticate(self, identifier, secret):
        """
        This method is abstract.

        :param str identifier: An identifer for the user, typically this is
            either a username or an email.
        :param str secret: A secret to verify the user is who they say they are
        :returns: A fully authenticated but not yet logged in user
        :rtype: :class:`User<flaskbb.user.models.User>`

        """
        pass


class AuthenticationProvider(ABC):
    """
    Used to provide an authentication service for FlaskBB.

    For example, an implementer may choose to use LDAP as an authentication
    source::

        class LDAPAuthenticationProvider(AuthenticationProvider):
            def __init__(self, ldap_client):
                self.ldap_client = ldap_client

            def authenticate(self, identifier, secret):
                user_dn = "uid={},ou=flaskbb,ou=org".format(identifier)
                try:
                    self.ldap_client.bind_user(user_dn, secret)
                    return User.query.join(
                            UserLDAP
                        ).filter(
                            UserLDAP.dn==user_dn
                        ).with_entities(User).one()
                except Exception:
                    return None

    During an authentication process, a provider may raise a
    :class:`StopAuthentication<flaskbb.core.auth.authentication.StopAuthentication>`
    exception to completely, but safely halt the process. This is most useful
    when multiple providers are being used.
    """

    @abstractmethod
    def authenticate(self, identifier, secret):
        """
        This method is abstract.

        :param str identifier: An identifer for the user, typically this is
            either a username or an email.
        :param str secret: A secret to verify the user is who they say they are
        :returns: An authenticated user.
        :rtype: :class:`User<flaskbb.user.models.User>`
        """
        pass

    def __call__(self, identifier, secret):
        return self.authenticate(identifier, secret)


class AuthenticationFailureHandler(ABC):
    """
    Used to post process authentication failures, such as no provider returning
    a user or a provider raising
    :class:`StopAuthentication<flaskbb.core.auth.authentication.StopAuthentication>`.

    Postprocessing may take many forms, such as incrementing the login attempts
    locking an account if too many attempts are made, forcing a reauth if
    the user is currently authenticated in a different session, etc.

    Failure handlers should not return a value as it will not be considered.
    """

    @abstractmethod
    def handle_authentication_failure(self, identifier):
        """
        This method is abstract.

        :param str identifier: An identifer for the user, typically this is
            either a username or an email.
        """
        pass

    def __call__(self, identifier):
        self.handle_authentication_failure(identifier)


class PostAuthenticationHandler(ABC):
    """
    Used to post process authentication success. Post authentication handlers
    recieve the user instance that was returned by the successful
    authentication rather than the identifer.

    Postprocessors may decide to preform actions such as flashing a message
    to the user, clearing failed login attempts, etc.

    Alternatively, a postprocessor can decide to fail the authentication
    process anyways by raising
    :class:`StopAuthentication<flaskbb.core.auth.authentication.StopAuthentication>`,
    for example a user may successfully authenticate but has not yet activated
    their account.

    Cancelling a successful authentication will cause registered
    :class:`~flaskbb.core.auth.authentication.AuthenticationFailureHandler`
    instances to be run.

    Success handlers should not return a value as it will not be considered.
    """

    @abstractmethod
    def handle_post_auth(self, user):
        """
        This method is abstact.

        :param user: An authenticated but not yet logged in user
        :type user: :class:`User<flaskbb.user.model.User>`
        """
        pass

    def __call__(self, user):
        self.handle_post_auth(user)


class ReauthenticateManager(ABC):
    """
    Used to handle the reauthentication process in FlaskBB. A default
    implementation is provided, however this is interface exists in case
    alternative flows are desired.

    Unlike the AuthenticationManager, there is no need to return the user to
    the caller.
    """

    @abstractmethod
    def reauthenticate(self, user, secret):
        """
        This method is abstract.

        :param user: The current user instance
        :param str secret: The secret provided by the user
        :type user: :class:`User<flaskbb.user.models.User>`
        """
        pass

    def __call__(self, user, secret):
        pass


class ReauthenticateProvider(ABC):
    """
    Used to reauthenticate a user that is already logged into the system,
    for example when suspicious activity is detected in their session.

    ReauthenticateProviders are similiar to
    :class:`~flaskbb.core.auth.authentication.AuthenticationProvider`
    except they receive a user instance rather than an identifer for a user.

    A successful reauthentication should return True while failures should
    return None in order to give other providers an attempt run.

    If a ReauthenticateProvider determines that reauthentication should
    immediately end, it may raise
    :class:~flaskbb.core.auth.authentication.StopAuthentication`
    to safely end the process.


    An example::

        class LDAPReauthenticateProvider(ReauthenticateProvider):
            def __init__(self, ldap_client):
                self.ldap_client = ldap_client

            def reauthenticate(self, user, secret):
                user_dn = "uid={},ou=flaskbb,ou=org".format(user.username)
                try:
                    self.ldap_client.bind_user(user_dn, secret)
                    return True
                except Exception:
                    return None

    """

    @abstractmethod
    def reauthenticate(self, user, secret):
        """
        This method is abstract.

        :param user: The current user instance
        :param str secret: The secret provided by the user
        :type user: :class:`User<flaskbb.user.models.User>`
        :returns: True for a successful reauth, otherwise None
        """

        pass

    def __call__(self, user, secret):
        self.handle_reauth(user, secret)


class ReauthenticateFailureHandler(ABC):
    """
    Used to manager reauthentication failures in FlaskBB.

    ReauthenticateFailureHandlers are similiar to
    :class:`~flaskbb.core.auth.authentication.AuthenticationFailureHandler`
    except they receive the user instance rather than an indentifier for a user
    """

    @abstractmethod
    def handle_reauth_failure(self, user):
        """
        This method is abstract.

        :param user: The current user instance that failed the reauth attempt
        :type user: :class:`User<flaskbb.user.models.User>`
        """
        pass

    def __call__(self, user):
        self.handle_reauth_failure(user)


class PostReauthenticateHandler(ABC):
    """
    Used to post process successful reauthentication attempts.

    PostAuthenticationHandlers are similar to
    :class:`~flaskbb.core.auth.authentication.PostAuthenticationHandler`,
    including their ability to cancel a successful attempt by raising
    :class:`StopAuthentication<flaskbb.core.auth.authentication.StopAuthentication>`
    """

    @abstractmethod
    def handle_post_reauth(self, user):
        """
        This method is abstract.

        :param user: The current user instance that passed the reauth attempt
        :type user: :class:`User<flaskbb.user.models.User>`
        """
        pass

    def __call__(self, user):
        self.handle_post_reauth(user)
