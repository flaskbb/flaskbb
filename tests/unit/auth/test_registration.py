import pytest

from flaskbb.auth.services import registration
from flaskbb.core.auth.registration import UserRegistrationInfo
from flaskbb.core.exceptions import StopValidation, ValidationError
from flaskbb.core.user.repo import UserRepository


class RaisingValidator(registration.UserValidator):

    def validate(self, user_info):
        raise ValidationError('test', 'just a little whoopsie-diddle')


def test_doesnt_register_user_if_validator_fails_with_ValidationError(mocker):
    repo = mocker.Mock(UserRepository)
    service = registration.RegistrationService([RaisingValidator()], repo)

    with pytest.raises(StopValidation):
        service.register(
            UserRegistrationInfo(
                username='fred',
                password='lol',
                email='fred@fred.fred',
                language='fredspeak',
                group=4
            )
        )

    repo.add.assert_not_called()


def test_gathers_up_all_errors_during_registration(mocker):
    repo = mocker.Mock(UserRepository)
    service = registration.RegistrationService([
        RaisingValidator(), RaisingValidator()
    ], repo)

    with pytest.raises(StopValidation) as excinfo:
        service.register(
            UserRegistrationInfo(
                username='fred',
                password='lol',
                email='fred@fred.fred',
                language='fredspeak',
                group=4
            )
        )

    repo.add.assert_not_called()
    assert len(excinfo.value.reasons) == 2
    assert all(('test', 'just a little whoopsie-diddle') == r
               for r in excinfo.value.reasons)


def test_registers_user_if_no_errors_occurs(mocker):
    repo = mocker.Mock(UserRepository)
    service = registration.RegistrationService([], repo)
    user_info = UserRegistrationInfo(
        username='fred',
        password='lol',
        email='fred@fred.fred',
        language='fredspeak',
        group=4
    )
    service.register(user_info)
    repo.add.assert_called_with(user_info)
