# -*- coding: utf -*-
"""
    flaskbb.tokens.serializer
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

from datetime import timedelta

from itsdangerous import (BadData, BadSignature, SignatureExpired,
                          TimedJSONWebSignatureSerializer)

from ..core import tokens


_DEFAULT_EXPIRY = timedelta(hours=1)


class FlaskBBTokenSerializer(tokens.TokenSerializer):
    """
    Default token serializer for FlaskBB. Generates JWTs
    that are time sensitive. By default they will expire after
    1 hour.

    It creates tokens from flaskbb.core.tokens.Token instances
    and creates instances of that class when loading tokens.

    When loading a token, if an error occurs related to the
    token itself, a flaskbb.core.tokens.TokenError will be
    raised. Exceptions not caused by parsing the token
    are simply propagated.

    :str secret_key: The secret key used to sign the tokens
    :timedelta expiry: Expiration of tokens
    """

    def __init__(self, secret_key, expiry=_DEFAULT_EXPIRY):
        self._serializer = TimedJSONWebSignatureSerializer(
            secret_key, int(expiry.total_seconds())
        )

    def dumps(self, token):
        """
        Transforms an instance of flaskbb.core.tokens.Token into
        a text serialized JWT.

        :flaskbb.core.tokens.Token token: Token to transformed into a JWT
        :returns str: A fully serialized token
        """
        return self._serializer.dumps(
            {
                'id': token.user_id,
                'op': token.operation,
            }
        )

    def loads(self, raw_token):
        """
        Transforms a JWT into a flaskbb.core.tokens.Token.

        If a token is invalid due to it being malformed,
        tampered with or expired, a flaskbb.core.tokens.TokenError
        is raised. Errors not related to token parsing are
        simply propagated.

        :str raw_token: JWT to be parsed
        :returns flaskbb.core.tokens.Token: Parsed token
        """
        try:
            parsed = self._serializer.loads(raw_token)
        except SignatureExpired:
            raise tokens.TokenError.expired()
        except BadSignature:  # pragma: no branch
            raise tokens.TokenError.invalid()
        # ideally we never end up here as BadSignature should
        # catch everything else, however since this is the root
        # exception for itsdangerous we'll catch it down and
        # and re-raise our own
        except BadData:  # pragma: no cover
            raise tokens.TokenError.bad()
        else:
            return tokens.Token(user_id=parsed['id'], operation=parsed['op'])
