# -*- coding: utf-8 -*-
"""
    flaskbb.core.auth.password
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Interfaces and services for auth services
    related to password.

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""
from abc import ABC, abstractmethod


class ResetPasswordService(ABC):
    """
    Interface for managing the password reset experience in FlaskBB.
    """

    @abstractmethod
    def initiate_password_reset(self, email):
        """
        This method is abstract.

        Used to send a password reset token to a user.

        This method may raise a
        :class:`ValidationError<flaskbb.core.exceptions.ValidationError>`
        when generating the token, such as when the user requests a reset token
        be sent to an email that isn't registered in the application.

        :param str email: The email to send the reset request to.
        """
        pass

    @abstractmethod
    def reset_password(self, token, email, new_password):
        """
        This method is abstract.

        Used to process a password reset token and handle resetting the user's
        password to the newly desired one. The token passed to this message
        is the raw, serialized token sent to the user.

        This method may raise
        :class:`TokenError<flaskbb.core.tokens.TokenError>` or
        :class:`ValidationError<flaskbb.core.exceptions.ValidationError>`
        to communicate failures when parsing or consuming the token.

        :param str token: The raw serialized token sent to the user
        :param str email: The email entered by the user at password reset
        :param str new_password: The new password to assign to the user
        """
        pass
