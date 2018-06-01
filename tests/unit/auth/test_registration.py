import pytest
from pluggy import HookimplMarker

from flaskbb.auth.services.registration import RegistrationService
from flaskbb.core.auth.registration import (
    RegistrationFailureHandler,
    RegistrationPostProcessor,
    UserRegistrationInfo,
    UserValidator,
)
from flaskbb.core.exceptions import (
    PersistenceError,
    StopValidation,
    ValidationError,
)
from flaskbb.user.models import User

pytestmark = pytest.mark.usefixtures("default_settings")


class RaisingValidator(UserValidator):

    def validate(self, user_info):
        raise ValidationError("username", "nope")


class TestRegistrationService(object):
    fred = UserRegistrationInfo(
        username="Fred",
        password="Fred",
        email="fred@fred.com",
        language="fred",
        group=4,
    )

    def test_raises_stop_validation_if_validators_fail(
        self, plugin_manager, database
    ):
        service = self._get_service(plugin_manager, database)
        plugin_manager.register(self.impls(validator=RaisingValidator()))

        with pytest.raises(StopValidation) as excinfo:
            service.register(self.fred)

        assert ("username", "nope") in excinfo.value.reasons

    def test_calls_failure_handlers_if_validation_fails(
        self, plugin_manager, database, mocker
    ):
        service = self._get_service(plugin_manager, database)
        failure = mocker.MagicMock(spec=RegistrationFailureHandler)
        plugin_manager.register(
            self.impls(validator=RaisingValidator(), failure=failure)
        )

        with pytest.raises(StopValidation) as excinfo:
            service.register(self.fred)

        failure.assert_called_once_with(self.fred, excinfo.value.reasons)

    def test_registers_user_if_everything_is_good(
        self, database, plugin_manager
    ):
        service = self._get_service(plugin_manager, database)

        service.register(self.fred)

        actual_fred = User.query.filter(User.username == "Fred").one()

        assert actual_fred.id is not None

    def test_calls_post_processors_if_user_registration_works(
        self, database, plugin_manager, mocker
    ):
        service = self._get_service(plugin_manager, database)
        post_process = mocker.MagicMock(spec=RegistrationPostProcessor)
        plugin_manager.register(self.impls(post_process=post_process))

        fred = service.register(self.fred)

        post_process.assert_called_once_with(fred)

    def test_raises_persistenceerror_if_saving_user_goes_wrong(
        self, database, plugin_manager, Fred
    ):
        service = self._get_service(plugin_manager, database)

        with pytest.raises(PersistenceError):
            service.register(self.fred)

    @staticmethod
    def _get_service(plugin_manager, db):
        return RegistrationService(plugins=plugin_manager, users=User, db=db)

    @staticmethod
    def impls(validator=None, failure=None, post_process=None):
        impl = HookimplMarker("flaskbb")

        class Impls:
            if validator is not None:

                @impl
                def flaskbb_gather_registration_validators(self):
                    return [validator]

            if failure is not None:

                @impl
                def flaskbb_registration_failure_handler(
                    self, user_info, failures
                ):
                    failure(user_info, failures)

            if post_process is not None:

                @impl
                def flaskbb_registration_post_processor(self, user):
                    post_process(user)

        return Impls()
