"""
    flaskbb.auth.password
    ~~~~~~~~~~~~~~~~~~~~~

    Password reset manager

    :copyright: (c) 2014-2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

from flask_babelplus import gettext as _

from ...core.auth.password import ResetPasswordService as _ResetPasswordService
from ...core.exceptions import StopValidation, ValidationError
from ...core.tokens import Token, TokenActions, TokenError
from ...email import send_reset_token


class ResetPasswordService(_ResetPasswordService):
    """
    Default password reset handler for FlaskBB, manages the process through
    email.
    """

    def __init__(self, token_serializer, users, token_verifiers):
        self.token_serializer = token_serializer
        self.users = users
        self.token_verifiers = token_verifiers

    def initiate_password_reset(self, email):
        """
        Looks up a user by email and raises a
        :class:`ValidationError<flaskbb.core.exceptions.ValidationError>`
        if that user does not exist, otherwise generates a reset password
        token and emails it to the user.
        """

        user = self.users.query.filter_by(email=email).first()

        if user is None:
            raise ValidationError('email', _('Invalid email'))

        token = self.token_serializer.dumps(
            Token(user_id=user.id, operation=TokenActions.RESET_PASSWORD)
        )

        send_reset_token.delay(
            token=token, username=user.username, email=user.email
        )

    def reset_password(self, token, email, new_password):
        """
        Resets a user's password if the email entered by the user matches
        the email on file for the user in FlaskBB.

        If the provided token is not a reset password token, then it raises a
        :class:`TokenError<flaskbb.core.tokens.TokenError>` and if the
        information provided by the user does not meet criteria defined
        by the passed token verifiers, then a
        :class:`StopValidation<flaskbb.core.exceptions.StopValidation>` is
        raised.
        """

        token = self.token_serializer.loads(token)
        if token.operation != TokenActions.RESET_PASSWORD:
            raise TokenError.invalid()
        self._verify_token(token, email)
        user = self.users.query.get(token.user_id)
        user.password = new_password

    def _verify_token(self, token, email):
        errors = []

        for verifier in self.token_verifiers:
            try:
                verifier(token, email=email)
            except ValidationError as e:
                errors.append((e.attribute, e.reason))

        if errors:
            raise StopValidation(errors)
