# -*- coding: utf-8 -*-
"""
    flaskbb.core.auth.password
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Interfaces and services for auth services
    related to password.

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

from abc import abstractmethod

from ..._compat import ABC


class ResetPasswordService(ABC):
    """
    Interface for managing the password reset experience in FlaskBB.
    """

    @abstractmethod
    def initiate_password_reset(self, email):
        """
        Used to send a password reset token to a user. This may take any form
        but it is recommended to use a permanent communication such as email.

        This method may raise a :class:`flaskbb.core.exceptions.ValidationError`
        when generating the token, such as when the user requests a reset token
        be sent to an email that isn't registered in the application.
        """
        pass

    @abstractmethod
    def reset_password(self, token, email, new_password):
        """
        Used to process a password reset token and handle resetting the user's
        password to the newly desired one. The token passed to this message
        is the raw, serialized token sent to the user.

        This method may raise
        :class:`flaskbb.core.tokens.TokenError` and
        :class:`flaskbb.core.exceptions.ValidationError` to communicate
        failures when parsing or consuming the token.
        """
        pass
