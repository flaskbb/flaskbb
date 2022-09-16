# -*- coding: utf-8 -*-
"""
    flaskbb.core.auth.tokens
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module provides ways of interacting
    with tokens in FlaskBB

    :copyright: (c) 2014-2018 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""
from abc import ABC, abstractmethod

import attr
from flask_babelplus import gettext as _

from .exceptions import BaseFlaskBBError


class TokenError(BaseFlaskBBError):
    """
    Raised when there is an issue with deserializing
    a token. Has helper classmethods to ensure
    consistent verbiage.

    :param str reason: An explanation of why the token is invalid
    """

    def __init__(self, reason):
        self.reason = reason
        super(TokenError, self).__init__(reason)

    @classmethod
    def invalid(cls):
        """
        Used to raise an exception about a token that is invalid
        due to being signed incorrectly, has been tampered with,
        is unparsable or contains an inappropriate action.
        """
        return cls(_('Token is invalid'))

    @classmethod
    def expired(cls):
        """
        Used to raise an exception about a token that has expired and is
        no longer usable.
        """
        return cls(_('Token is expired'))

    # in theory this would never be raised
    # but it's provided for a generic catchall
    # when processing goes horribly wrong
    @classmethod  # pragma: no cover
    def bad(cls):
        return cls(_('Token cannot be processed'))


# holder for token actions
# not an enum so plugins can add to it
class TokenActions:
    """
    Collection of token actions.

    .. note::
        This is just a class rather than an enum because enums cannot be
        extended at runtime which would limit the number of token actions
        to the ones implemented by FlaskBB itself and block extension of
        tokens by plugins.
    """
    RESET_PASSWORD = 'reset_password'
    ACTIVATE_ACCOUNT = 'activate_account'


@attr.s(frozen=True, eq=True, order=True, hash=True)
class Token(object):
    """
    :param int user_id:
    :param str operation: An operation taken from
        :class:`TokenActions<flaskbb.core.tokens.TokenActions>`
    """
    user_id = attr.ib()
    operation = attr.ib()


class TokenSerializer(ABC):
    """

    """

    @abstractmethod
    def dumps(self, token):
        """
        This method is abstract.

        Used to transform a token into a string representation of it.

        :param token:
        :type token: :class:`Token<flaskbb.core.tokens.Token>`
        :returns str:
        """
        pass

    @abstractmethod
    def loads(self, raw_token):
        """
        This method is abstract

        Used to transform a string representation of a token into an
        actual :class:`Token<flaskbb.core.tokens.Token>` instance

        :param str raw_token:
        :returns token: The parsed token
        :rtype: :class:`Token<flaskbb.core.tokens.Token`>
        """
        pass


class TokenVerifier(ABC):
    """
    Used to verify the validity of tokens post
    deserialization, such as an email matching the
    user id in the provided token.

    Should raise a
    :class:`ValidationError<flaskbb.core.exceptions.ValidationError>`
    if verification fails.
    """

    @abstractmethod
    def verify_token(self, token, **kwargs):
        """
        This method is abstract.

        :param token: The parsed token to verify
        :param kwargs: Arbitrary context for validation of the token
        :type token: :class:`Token<flaskbb.core.tokens.Token>`
        """
        pass

    def __call__(self, token, **kwargs):
        return self.verify_token(token, **kwargs)
