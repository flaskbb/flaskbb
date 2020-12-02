# -*- coding: utf-8 -*-
"""
    flaskbb.core.auth.activation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Interfaces for handling account activation
    in FlaskBB

    :copyright: (c) 2014-2018 the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""
from abc import ABC, abstractmethod


class AccountActivator(ABC):
    """
    Interface for managing account activation in installations that require
    a user to activate their account before using it.
    """

    @abstractmethod
    def initiate_account_activation(self, user):
        """
        This method is abstract.

        Used to extend an offer of activation to the user. This may take any
        form, but is recommended to take the form of a permanent communication
        such as email.

        This method may raise
        :class:`ValidationError<flaskbb.core.exceptions.ValidationError>`
        to communicate a failure when creating the token for the user to
        activate their account with (such as when a user has requested a token
        be sent to an email that is not registered in the installation or
        the account associated with that email has already been activated).

        :param user: The user that the activation request applies to.
        :type user: :class:`User<flaskbb.user.models.User>`
        """
        pass

    @abstractmethod
    def activate_account(self, token):
        """
        This method is abstract.

        Used to handle the actual activation of an account. The token
        passed in is the serialized token communicated to the user to use
        for activation. This method may raise
        :class:`TokenError<flaskbb.core.tokens.TokenError>` or
        :class:`ValidationError<flaskbb.core.exceptions.ValidationError>`
        to communicate failures when parsing or consuming the token.

        :param str token: The raw serialized token sent to the user
        """
        pass
