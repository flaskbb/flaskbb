# -*- coding: utf-8 -*-
"""
    flaskbb.utils.tokens
    ~~~~~~~~~~~~~~~~~~~~

    A module that helps to create and verify various tokens that
    are used by FlaskBB.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
from flask import current_app
from itsdangerous import (TimedJSONWebSignatureSerializer, SignatureExpired,
                          BadSignature)

from flaskbb.user.models import User


logger = logging.getLogger(__name__)


def make_token(user, operation, expire=3600):
    """Generates a JSON Web Signature (JWS).
    See `RFC 7515 <https://tools.ietf.org/html/rfc7515>` if you want to know
    more about JWS.

    :param user: The user object for whom the token should be generated.
    :param operation: The function of the token. For example, you might want
                      to generate two different tokens. One for a
                      password reset link, which you hypothetically want
                      to name 'reset' and the second one, for the generation
                      of a token for a E-Mail confirmation link, which you
                      name 'email'.
    :param expire: The time, in seconds, after which the token should be
                   invalid. Defaults to 3600.
    """
    s = TimedJSONWebSignatureSerializer(
        current_app.config['SECRET_KEY'], expire
    )
    data = {"id": user.id, "op": operation}
    return s.dumps(data)


def get_token_status(token, operation, return_data=False):
    """Returns the expired status, invalid status, the user and optionally
    the content of the JSON Web Signature token.

    :param token: A valid JSON Web Signature token.
    :param operation: The function of the token.
    :param return_data: If set to ``True``, it will also return the content
                        of the token.
    """
    s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
    user, data = None, None
    expired, invalid = False, False

    try:
        data = s.loads(token)
    except SignatureExpired:
        expired = True
    except (BadSignature, TypeError, ValueError):
        invalid = True

    if data is not None:
        # check if the operation matches the one from the token
        if operation == data.get("op", None):
            user = User.query.filter_by(id=data.get('id')).first()
        else:
            invalid = True

    if return_data:
        return expired, invalid, user, data

    return expired, invalid, user
