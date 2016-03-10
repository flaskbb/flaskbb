# -*- coding: utf-8 -*-
"""
    flaskbb.utils.tokens
    ~~~~~~~~~~~~~~~~~~~~

    A module that helps to create and verify various tokens that
    are used by FlaskBB.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import current_app
from itsdangerous import (TimedJSONWebSignatureSerializer, SignatureExpired,
                          BadSignature)

from flaskbb.user.models import User


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


def get_token_status(token, operation, return_data):
    """Returns the expired status, invalid status, the user and optionally
    the content of the JSON Web Signature token.

    :param token: A valid JSON Web Signature token.
    :param operation: The function of the token.
    :param return_data: If set to ``True``, it will also return the content
                        of the token.
    """
    s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
    user, data = None
    expired, invalid = False, False

    try:
        data = s.loads(token)
    except SignatureExpired:
        expired = True
    except (BadSignature, TypeError, ValueError):
        invalid = True

    if data:
        user = User.query.filter_by(id=data.get('id')).first()

    expired = expired and (user is not None)

    if return_data:
        return expired, invalid, user, data

    return expired, invalid, user


def generate_email_confirmation_token(user):
    """Generates a E-Mail confirmation token."""
    return make_token(user=user, operation="confirm_email")


def generate_password_reset_token(user):
    """Generates a password reset token."""
    return make_token(user=user, operation="reset_password")
