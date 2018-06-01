from flask import get_flashed_messages
from flask_login import current_user

from flaskbb.auth.services.registration import (
    AutoActivateUserPostProcessor,
    AutologinPostProcessor,
    SendActivationPostProcessor,
)
from flaskbb.core.auth.activation import AccountActivator
from flaskbb.utils.settings import flaskbb_config


class TestAutoActivateUserPostProcessor(object):

    def test_activates_when_user_activation_isnt_required(
        self, unactivated_user, database
    ):
        config = {"ACTIVATE_ACCOUNT": False}
        processor = AutoActivateUserPostProcessor(database, config)
        processor.post_process(unactivated_user)

        assert unactivated_user.activated

    def test_doesnt_activate_when_user_activation_is_required(
        self, database, unactivated_user
    ):
        config = {"ACTIVATE_ACCOUNT": True}
        processor = AutoActivateUserPostProcessor(database, config)
        processor.post_process(unactivated_user)

        assert not unactivated_user.activated


class TestAutologinPostProcessor(object):

    def test_sets_user_as_current_user(
        self, Fred, request_context, default_settings
    ):
        flaskbb_config["ACTIVATE_ACCOUNT"] = False
        processor = AutologinPostProcessor()

        processor.post_process(Fred)

        expected_message = ("success", "Thanks for registering.")

        assert current_user.username == Fred.username
        assert (
            get_flashed_messages(with_categories=True)[0] == expected_message
        )


class TestSendActivationPostProcessor(object):

    class SpyingActivator(AccountActivator):

        def __init__(self):
            self.called = False
            self.user = None

        def initiate_account_activation(self, user):
            self.called = True
            self.user = user

        def activate_account(self, token):
            pass

    def test_sends_activation_notice(
        self, request_context, unactivated_user, default_settings
    ):
        activator = self.SpyingActivator()
        processor = SendActivationPostProcessor(activator)

        processor.post_process(unactivated_user)

        expected_message = (
            "success",
            "An account activation email has been sent to notactive@example.com",  # noqa
        )
        assert activator.called
        assert activator.user == unactivated_user.email
        assert (
            get_flashed_messages(with_categories=True)[0] == expected_message
        )
