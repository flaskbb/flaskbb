import pytest

from flaskbb.auth.services import activation
from flaskbb.core.exceptions import ValidationError
from flaskbb.core.tokens import Token, TokenActions, TokenError
from flaskbb.user.models import User

pytestmark = pytest.mark.usefixtures('default_settings')


class TestAccountActivationInitiateActivation(object):

    def test_raises_if_user_doesnt_exist(self, Fred, token_serializer):
        service = activation.AccountActivator(token_serializer, User)

        with pytest.raises(ValidationError) as excinfo:
            service.initiate_account_activation('does@not.exist')

        assert excinfo.value.reason == "Entered email doesn't exist"

    def test_raises_if_user_is_already_active(self, Fred, token_serializer):
        service = activation.AccountActivator(token_serializer, User)

        with pytest.raises(ValidationError) as excinfo:
            service.initiate_account_activation(Fred.email)

        assert excinfo.value.reason == "Account is already activated"

    def test_calls_send_activation_token_successfully_if_user_exists(
            self, mocker, unactivated_user, token_serializer
    ):
        service = activation.AccountActivator(token_serializer, User)
        mock = mocker.MagicMock()
        mocker.patch(
            'flaskbb.auth.services.activation.send_activation_token.delay',
            mock
        )
        service.initiate_account_activation(unactivated_user.email)

        token = token_serializer.dumps(
            Token(
                user_id=unactivated_user.id,
                operation=TokenActions.ACTIVATE_ACCOUNT
            )
        )
        mock.assert_called_once_with(
            token=token,
            username=unactivated_user.username,
            email=unactivated_user.email
        )


class TestAccountActivationActivateAccount(object):

    def test_raises_if_token_operation_isnt_activate(self, token_serializer):
        service = activation.AccountActivator(token_serializer, User)
        token = token_serializer.dumps(
            Token(user_id=1, operation=TokenActions.RESET_PASSWORD)
        )

        with pytest.raises(TokenError):
            service.activate_account(token)

    def test_raises_if_user_is_already_active(self, Fred, token_serializer):
        service = activation.AccountActivator(token_serializer, User)
        token = token_serializer.dumps(
            Token(user_id=Fred.id, operation=TokenActions.ACTIVATE_ACCOUNT)
        )

        with pytest.raises(ValidationError) as excinfo:
            service.activate_account(token)

        assert excinfo.value.reason == 'Account is already activated'

    def test_activates_user_successfully(
            self, unactivated_user, token_serializer
    ):
        service = activation.AccountActivator(token_serializer, User)
        token = token_serializer.dumps(
            Token(
                user_id=unactivated_user.id,
                operation=TokenActions.ACTIVATE_ACCOUNT
            )
        )
        service.activate_account(token)
        assert unactivated_user.activated
