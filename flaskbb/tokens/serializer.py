# -*- coding: utf -*-
"""
    flaskbb.tokens.serializer
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

from datetime import datetime, timedelta

import jwt

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
        self.secret_key = secret_key
        self.algorithm = "HS256"

        if isinstance(expiry, timedelta):
            self.expiry = datetime.utcnow() + expiry
        elif isinstance(expiry, datetime):
            self.expiry = expiry
        else:
            raise TypeError("'expiry' must be of type timedelta or datetime")

    def dumps(self, token):
        """
        Transforms an instance of flaskbb.core.tokens.Token into
        a text serialized JWT.

        :flaskbb.core.tokens.Token token: Token to transformed into a JWT
        :returns str: A fully serialized token
        """
        return jwt.encode(
            payload={"id": token.user_id, "op": token.operation, "exp": self.expiry},
            key=self.secret_key,
            algorithm=self.algorithm,
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
            parsed = jwt.decode(
                raw_token, key=self.secret_key, algorithms=[self.algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise tokens.TokenError.expired()
        except jwt.DecodeError:  # pragma: no branch
            raise tokens.TokenError.invalid()
        # ideally we never end up here as DecodeError should
        # catch everything else, however since this is the root
        # exception for PyJWT we'll catch it down and
        # and re-raise our own
        except jwt.InvalidTokenError:  # pragma: no cover
            raise tokens.TokenError.bad()
        else:
            return tokens.Token(user_id=parsed["id"], operation=parsed["op"])
