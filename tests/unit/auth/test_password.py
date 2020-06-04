import pytest
from werkzeug.security import check_password_hash

from flaskbb.auth.services import password
from flaskbb.core.exceptions import StopValidation, ValidationError
from flaskbb.core.tokens import Token, TokenActions, TokenError
from flaskbb.user.models import User

pytestmark = pytest.mark.usefixtures('default_settings')


class TestPasswordReset(object):

    def test_raises_token_error_if_not_a_password_reset(
            self, token_serializer
    ):
        service = password.ResetPasswordService(token_serializer, User, [])
        raw_token = token_serializer.dumps(
            Token(user_id=1, operation=TokenActions.ACTIVATE_ACCOUNT)
        )

        with pytest.raises(TokenError) as excinfo:
            service.reset_password(
                raw_token, "some@e.mail", "a great password!"
            )

        assert "invalid" in str(excinfo.value)

    def test_raises_StopValidation_if_verifiers_fail(self, token_serializer):
        token = token_serializer.dumps(
            Token(user_id=1, operation=TokenActions.RESET_PASSWORD)
        )

        def verifier(*a, **k):
            raise ValidationError('attr', 'no')

        service = password.ResetPasswordService(
            token_serializer, User, [verifier]
        )

        with pytest.raises(StopValidation) as excinfo:
            service.reset_password(token, "an@e.mail", "great password!")
        assert ("attr", "no") in excinfo.value.reasons

    def test_sets_user_password_to_provided_if_verifiers_pass(
            self, token_serializer, Fred
    ):
        token = token_serializer.dumps(
            Token(user_id=Fred.id, operation=TokenActions.RESET_PASSWORD)
        )

        service = password.ResetPasswordService(token_serializer, User, [])

        service.reset_password(token, Fred.email, "newpasswordwhodis")
        assert check_password_hash(Fred.password, "newpasswordwhodis")

    # need fred to initiate Users
    def test_initiate_raises_if_user_doesnt_exist(
            self, token_serializer, Fred
    ):
        service = password.ResetPasswordService(token_serializer, User, [])
        with pytest.raises(ValidationError) as excinfo:
            service.initiate_password_reset('lol@doesnt.exist')

        assert excinfo.value.attribute == 'email'
        assert excinfo.value.reason == 'Invalid email'

    def test_calls_send_reset_token_successfully_if_user_exists(
            self, Fred, mocker, token_serializer
    ):
        service = password.ResetPasswordService(token_serializer, User, [])
        mock = mocker.MagicMock()

        mocker.patch(
            'flaskbb.auth.services.password.send_reset_token.delay',
            mock
        )
        service.initiate_password_reset(Fred.email)

        token = token_serializer.dumps(
            Token(user_id=Fred.id, operation=TokenActions.RESET_PASSWORD)
        )
        mock.assert_called_once_with(
            token=token, username=Fred.username, email=Fred.email
        )
