from uuid import uuid4

import pytest
from flaskbb.core.exceptions import StopValidation, ValidationError
from flaskbb.core.user.update import EmailUpdate, PasswordUpdate
from flaskbb.user.models import User
from flaskbb.user.services import validators

pytestmark = pytest.mark.usefixtures("default_settings")


class TestEmailsMustBeDifferent:
    def test_raises_if_emails_match(self, Fred):
        matching_emails = EmailUpdate("same@email.example", Fred.email)

        with pytest.raises(ValidationError) as excinfo:
            validators.EmailsMustBeDifferent().validate(Fred, matching_emails)
        assert "New email address must be different" in str(excinfo.value)

    def test_doesnt_raise_if_emails_are_different(self, Fred):
        different_emails = EmailUpdate("old@email.example", "new@email.example")

        validators.EmailsMustBeDifferent().validate(Fred, different_emails)


class TestPasswordsMustBeDifferent:
    def test_raises_if_passwords_are_the_same(self, Fred):
        change = PasswordUpdate("fred", "fred")

        with pytest.raises(ValidationError) as excinfo:
            validators.PasswordsMustBeDifferent().validate(Fred, change)

        assert "New password must be different" in str(excinfo.value)

    def test_doesnt_raise_if_passwords_dont_match(self, Fred):
        change = PasswordUpdate("fred", "actuallycompletelydifferent")

        validators.PasswordsMustBeDifferent().validate(Fred, change)


class TestCantShareEmailValidator:
    def test_raises_if_email_is_already_registered(self, Fred, user):
        change = EmailUpdate("old@email.example", user.email)

        with pytest.raises(ValidationError) as excinfo:
            validators.CantShareEmailValidator(User).validate(Fred, change)

        assert "is already registered" in str(excinfo.value)

    def test_doesnt_raise_if_email_isnt_registered(self, Fred):
        change = EmailUpdate("old@email.example", "new@email.example")

        validators.CantShareEmailValidator(User).validate(Fred, change)


class TestOldEmailMustMatchValidator:
    def test_raises_if_old_email_doesnt_match(self, Fred):
        change = EmailUpdate("not@the.same.one.bit", "probably@real.email.provider")

        with pytest.raises(StopValidation) as excinfo:
            validators.OldEmailMustMatch().validate(Fred, change)

        assert [("old_email", "Old email does not match")] == excinfo.value.reasons

    def test_doesnt_raise_if_old_email_matches(self, Fred):
        change = EmailUpdate(Fred.email, "probably@real.email.provider")

        validators.OldEmailMustMatch().validate(Fred, change)


class TestOldPasswordMustMatchValidator:
    def test_raises_if_old_password_doesnt_match(self, Fred):
        change = PasswordUpdate(str(uuid4()), str(uuid4()))

        with pytest.raises(StopValidation) as excinfo:
            validators.OldPasswordMustMatch().validate(Fred, change)

        assert [("old_password", "Old password is wrong")] == excinfo.value.reasons

    def test_doesnt_raise_if_old_passwords_match(self, Fred):
        change = PasswordUpdate("fred", str(uuid4()))
        validators.OldPasswordMustMatch().validate(Fred, change)
