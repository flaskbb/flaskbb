# -*- utf-8 -*-
"""
flaskbb.tokens.verifiers
~~~~~~~~~~~~~~~~~~~~~~~~
Token verifier implementations

:copyright: (c) 2014-2018 the FlaskBB Team
:license: BSD, see LICENSE for more details
"""

from sqlalchemy import select

from flaskbb.extensions import db
from flaskbb.user.models import User

from ..core.exceptions import ValidationError
from ..core.tokens import TokenVerifier


class EmailMatchesUserToken(TokenVerifier):
    """
    Ensures that the token submitted for use matches
    the email entered by the user.

    :param User: User model for querying against
    """

    def __init__(self, users):
        self.users = users

    def verify_token(self, token, email, **kwargs):
        user = db.session.execute(select(User).where(User.id == token.user_id)).scalar()
        if user.email.lower() != email.lower():
            raise ValidationError("email", "Wrong email")
