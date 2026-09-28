"""
flaskbb.auth.services.activation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Handlers for activating accounts in FlaskBB

:copyright: (c) 2014-2018 the FlaskBB Team
:license: BSD, see LICENSE for more details
"""

from typing import override

import sqlalchemy as sa
from flask_babelplus import gettext as _

from ...core.auth.activation import AccountActivator as _AccountActivator
from ...core.exceptions import ValidationError
from ...core.tokens import Token, TokenActions, TokenError, TokenSerializer
from ...email import send_activation_token
from ...extensions import db
from ...user.models import User


class AccountActivator(_AccountActivator):
    """
    Default account activator for FlaskBB, handles the activation
    process through email.
    """

    def __init__(self, token_serializer: TokenSerializer, users: type[User]):
        self.token_serializer = token_serializer
        self.users = users

    @override
    def initiate_account_activation(self, email: str):
        user = db.session.execute(sa.select(self.users).filter_by(email=email)).scalar_one_or_none()

        if user is None:
            raise ValidationError("email", _("Entered email doesn't exist"))

        if user.activated:
            raise ValidationError("email", _("Account is already activated"))

        token = self.token_serializer.dumps(
            Token(user_id=user.id, operation=TokenActions.ACTIVATE_ACCOUNT)
        )

        send_activation_token.delay(token=token, username=user.username, email=user.email)  # pyright: ignore[reportUnknownMemberType]

    @override
    def activate_account(self, token: str):
        parsed_token = self.token_serializer.loads(token)
        if parsed_token.operation != TokenActions.ACTIVATE_ACCOUNT:
            raise TokenError.invalid()
        user = db.session.execute(
            sa.select(self.users).filter_by(id=parsed_token.user_id)
        ).scalar_one_or_none()
        if user is None:
            raise TokenError.invalid()
        if user.activated:
            raise ValidationError("activated", _("Account is already activated"))
        user.activated = True
