# -*- utf-8 -*-
"""
flaskbb.tokens.verifiers
~~~~~~~~~~~~~~~~~~~~~~~~
Token verifier implementations

:copyright: (c) 2014-2018 the FlaskBB Team
:license: BSD, see LICENSE for more details
"""

from typing import Any, override

from sqlalchemy import select

from flaskbb.extensions import db
from flaskbb.user.models import User

from ..core.exceptions import ValidationError
from ..core.tokens import Token, TokenVerifier


class EmailMatchesUserToken(TokenVerifier):
    """
    Ensures that the token submitted for use matches
    the email entered by the user.

    :param User: User model for querying against
    """

    def __init__(self, users: type[User]):
        self.users = users

    @override
    def verify_token(self, token: Token, *, email: str, **kwargs: Any) -> None:
        user = db.session.execute(select(User).where(User.id == token.user_id)).scalar()
        if not user:
            raise ValidationError("email", "User not found")

        if user.email.lower() != email.lower():
            raise ValidationError("email", "Wrong email")
