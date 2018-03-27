import pytest

from flaskbb.auth.services.registration import (EmailUniquenessValidator,
                                                UsernameRequirements,
                                                UsernameUniquenessValidator,
                                                UsernameValidator)
from flaskbb.core.auth.registration import UserRegistrationInfo
from flaskbb.core.exceptions import ValidationError
from flaskbb.user.models import User

pytestmark = pytest.mark.usefixtures('default_settings')


def test_raises_if_username_too_short():
    requirements = UsernameRequirements(min=4, max=100, blacklist=set())
    validator = UsernameValidator(requirements)

    registration = UserRegistrationInfo(
        username='no', password='no', email='no@no.no', group=4, language='no'
    )

    with pytest.raises(ValidationError) as excinfo:
        validator(registration)

    assert excinfo.value.attribute == 'username'
    assert 'must be between' in excinfo.value.reason


def test_raises_if_username_too_long():
    requirements = UsernameRequirements(min=0, max=1, blacklist=set())
    validator = UsernameValidator(requirements)

    registration = UserRegistrationInfo(
        username='no', password='no', email='no@no.no', group=4, language='no'
    )

    with pytest.raises(ValidationError) as excinfo:
        validator(registration)

    assert excinfo.value.attribute == 'username'
    assert 'must be between' in excinfo.value.reason


def test_raises_if_username_in_blacklist():
    requirements = UsernameRequirements(min=1, max=100, blacklist=set(['no']))
    validator = UsernameValidator(requirements)

    registration = UserRegistrationInfo(
        username='no', password='no', email='no@no.no', group=4, language='no'
    )

    with pytest.raises(ValidationError) as excinfo:
        validator(registration)

    assert excinfo.value.attribute == 'username'
    assert 'forbidden username' in excinfo.value.reason


# fred's back. :(
def test_raises_if_user_already_registered(Fred):
    validator = UsernameUniquenessValidator(User)
    registration = UserRegistrationInfo(
        username='fred',
        email='fred@fred.fred',
        language='fred',
        group=4,
        password='fred'
    )

    with pytest.raises(ValidationError) as excinfo:
        validator(registration)

    assert excinfo.value.attribute == 'username'
    assert 'already registered' in excinfo.value.reason


def test_raises_if_user_email_already_registered(Fred):
    validator = EmailUniquenessValidator(User)
    registration = UserRegistrationInfo(
        username='fred',
        email='fred@fred.fred',
        language='fred',
        group=4,
        password='fred'
    )

    with pytest.raises(ValidationError) as excinfo:
        validator(registration)

    assert excinfo.value.attribute == 'email'
    assert 'already registered' in excinfo.value.reason
