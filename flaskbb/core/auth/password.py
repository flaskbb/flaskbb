# -*- coding: utf-8 -*-
"""
    flaskbb.core.auth.password
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Interfaces and services for auth services
    related to password.

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

from ..exceptions import StopValidation, ValidationError
from ..tokens import TokenActions, TokenError


class ResetPasswordService(object):

    def __init__(self, token_serializer, users, token_verifiers):
        self.token_serializer = token_serializer
        self.users = users
        self.token_verifiers = token_verifiers

    def verify_token(self, token, email):
        errors = []

        for verifier in self.token_verifiers:
            try:
                verifier(token, email=email)
            except ValidationError as e:
                errors.append((e.attribute, e.reason))

        if errors:
            raise StopValidation(errors)

    def reset_password(self, token, email, new_password):
        token = self.token_serializer.loads(token)
        if token.operation != TokenActions.RESET_PASSWORD:
            raise TokenError.invalid()
        self.verify_token(token, email)
        user = self.users.query.get(token.user_id)
        user.password = new_password
