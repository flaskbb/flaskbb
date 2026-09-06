"""
flaskbb.auth.password
~~~~~~~~~~~~~~~~~~~~~

Password reset manager

:copyright: (c) 2014-2018 the FlaskBB Team.
:license: BSD, see LICENSE for more details
"""

from collections.abc import Sequence

import sqlalchemy as sa
from flask_babelplus import gettext as _

from ...core.auth.password import ResetPasswordService as _ResetPasswordService
from ...core.exceptions import StopValidation, ValidationError
from ...core.tokens import Token, TokenActions, TokenError, TokenSerializer, TokenVerifier
from ...email import send_reset_token
from ...extensions import db
from ...user.models import User


class ResetPasswordService(_ResetPasswordService):
    """
    Default password reset handler for FlaskBB, manages the process through
    email.
    """

    def __init__(
        self,
        token_serializer: TokenSerializer,
        users: type[User],
        token_verifiers: Sequence[TokenVerifier],
    ):
        self.token_serializer = token_serializer
        self.users = users
        self.token_verifiers = token_verifiers

    def initiate_password_reset(self, email: str):
        user = db.session.execute(sa.select(self.users).filter_by(email=email)).scalar_one_or_none()

        if user is None:
            raise ValidationError("email", _("Invalid email"))

        token = self.token_serializer.dumps(
            Token(user_id=user.id, operation=TokenActions.RESET_PASSWORD)
        )

        send_reset_token.delay(token=token, username=user.username, email=user.email)

    def reset_password(self, token: str, email: str, new_password: str):
        parsed_token = self.token_serializer.loads(token)
        if parsed_token.operation != TokenActions.RESET_PASSWORD:
            raise TokenError.invalid()
        self._verify_token(parsed_token, email)
        user = db.session.execute(
            sa.select(self.users).filter_by(id=parsed_token.user_id)
        ).scalar_one_or_none()
        if user is None:
            raise TokenError.invalid()
        user.password = new_password

    def _verify_token(self, token: Token, email: str):
        errors: list[tuple[str, str]] = []

        for verifier in self.token_verifiers:
            try:
                verifier(token, email=email)
            except ValidationError as e:
                errors.append((e.attribute, e.reason))

        if errors:
            raise StopValidation(errors)
