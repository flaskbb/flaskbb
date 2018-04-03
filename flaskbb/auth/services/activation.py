# -*- coding: utf-8 -*-
"""
    flaskbb.auth.services.activation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Handlers for activating accounts in FlaskBB

    :copyright: (c) 2014-2018 the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""

from flask_babelplus import gettext as _

from ...core.auth.activation import AccountActivator as _AccountActivator
from ...core.exceptions import ValidationError
from ...core.tokens import Token, TokenActions, TokenError
from ...email import send_activation_token


class AccountActivator(_AccountActivator):
    """
    Default account activator for FlaskBB, handles the activation
    process through email.
    """

    def __init__(self, token_serializer, users):
        self.token_serializer = token_serializer
        self.users = users

    def initiate_account_activation(self, email):
        user = self.users.query.filter_by(email=email).first()

        if user is None:
            raise ValidationError('email', _("Entered email doesn't exist"))

        if user.activated:
            raise ValidationError('email', _('Account is already activated'))

        token = self.token_serializer.dumps(
            Token(user_id=user.id, operation=TokenActions.ACTIVATE_ACCOUNT)
        )

        send_activation_token.delay(
            token=token, username=user.username, email=user.email
        )

    def activate_account(self, token):
        token = self.token_serializer.loads(token)
        if token.operation != TokenActions.ACTIVATE_ACCOUNT:
            raise TokenError.invalid()
        user = self.users.query.get(token.user_id)
        if user.activated:
            raise ValidationError(
                'activated', _('Account is already activated')
            )
        user.activated = True
