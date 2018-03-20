import json

import pytest
from flaskbb.core.auth import password
from flaskbb.core.exceptions import StopValidation, ValidationError
from flaskbb.core.tokens import Token, TokenActions, TokenError
from flaskbb.user.models import User
from werkzeug.security import check_password_hash


class SimpleTokenSerializer:

    @staticmethod
    def dumps(token):
        return json.dumps({'user_id': token.user_id, 'op': token.operation})

    @staticmethod
    def loads(raw_token):
        loaded = json.loads(raw_token)
        return Token(user_id=loaded['user_id'], operation=loaded['op'])


class TestPasswordReset(object):

    def test_raises_token_error_if_not_a_password_reset(self):
        service = password.ResetPasswordService(
            SimpleTokenSerializer, User, []
        )
        raw_token = SimpleTokenSerializer.dumps(
            Token(user_id=1, operation=TokenActions.ACTIVATE_ACCOUNT)
        )

        with pytest.raises(TokenError) as excinfo:
            service.reset_password(
                raw_token, "some@e.mail", "a great password!"
            )

        assert "invalid" in str(excinfo.value)

    def test_raises_StopValidation_if_verifiers_fail(self):
        token = SimpleTokenSerializer.dumps(
            Token(user_id=1, operation=TokenActions.RESET_PASSWORD)
        )

        def verifier(*a, **k):
            raise ValidationError('attr', 'no')

        service = password.ResetPasswordService(
            SimpleTokenSerializer, User, [verifier]
        )

        with pytest.raises(StopValidation) as excinfo:
            service.reset_password(token, "an@e.mail", "great password!")
        assert ("attr", "no") in excinfo.value.reasons

    def test_sets_user_password_to_provided_if_verifiers_pass(self, Fred):
        token = SimpleTokenSerializer.dumps(
            Token(user_id=Fred.id, operation=TokenActions.RESET_PASSWORD)
        )

        service = password.ResetPasswordService(
            SimpleTokenSerializer, User, []
        )

        service.reset_password(token, Fred.email, "newpasswordwhodis")
        assert check_password_hash(Fred.password, "newpasswordwhodis")
