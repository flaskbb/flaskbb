import pytest

from flaskbb.core.exceptions import ValidationError
from flaskbb.core.tokens import Token, TokenActions
from flaskbb.tokens import verifiers
from flaskbb.user.models import User

pytestmark = pytest.mark.usefixtures('default_settings')


def test_raises_if_email_doesnt_match_token_user(Fred):
    verifier = verifiers.EmailMatchesUserToken(User)
    token = Token(user_id=1, operation=TokenActions.RESET_PASSWORD)

    with pytest.raises(ValidationError) as excinfo:
        verifier(token, email="not really")

    assert excinfo.value.attribute == "email"
    assert excinfo.value.reason == "Wrong email"


def test_doesnt_raise_if_email_matches_token_user(Fred):
    verifier = verifiers.EmailMatchesUserToken(User)
    token = Token(user_id=Fred.id, operation=TokenActions.ACTIVATE_ACCOUNT)
    verifier(token, email=Fred.email)
