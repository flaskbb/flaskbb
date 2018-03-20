# -*- utf-8 -*-
"""
    flaskbb.tokens.verifiers
    ~~~~~~~~~~~~~~~~~~~~~~~~
    Token verifier implementations

    :copyright: (c) 2014-2018 the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""

from ..core.tokens import TokenVerifier
from ..core.exceptions import ValidationError


class EmailMatchesUserToken(TokenVerifier):
    """
    Ensures that the token submitted for use matches
    the email entered by the user.

    :param User: User model for querying against
    """
    def __init__(self, users):
        self.users = users

    def verify_token(self, token, email, **kwargs):
        user = self.users.query.get(token.user_id)
        if user.email.lower() != email.lower():
            raise ValidationError("email", "Wrong email")
