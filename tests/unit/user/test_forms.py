from datetime import date

import pytest
from werkzeug.datastructures import MultiDict

from flaskbb.core.user.update import (
    EmailUpdate,
    PasswordUpdate,
    SettingsUpdate,
    UserDetailsChange,
)
from flaskbb.user import forms

pytestmark = pytest.mark.usefixtures("post_request_context", "default_settings")


class TestGeneralSettingsForm(object):
    def test_transforms_to_expected_change_object(self):
        data = MultiDict({"language": "python", "theme": "molokai", "submit": True})

        form = forms.GeneralSettingsForm(formdata=data)

        expected = SettingsUpdate(language="python", theme="molokai")
        assert form.as_change() == expected


class TestChangeEmailForm(object):
    def test_transforms_to_expected_change_object(self, Fred):
        data = MultiDict(
            {
                "old_email": Fred.email,
                "new_email": "totally@real.email",
                "confirm_new_email": "totally@real.email",
                "submit": True,
            }
        )

        form = forms.ChangeEmailForm(Fred, formdata=data)
        expected = EmailUpdate(old_email=Fred.email, new_email="totally@real.email")

        assert form.as_change() == expected

    def test_valid_inputs(self, Fred):
        data = MultiDict(
            {
                "old_email": Fred.email,
                "new_email": "totally@real.email",
                "confirm_new_email": "totally@real.email",
                "submit": True,
            }
        )

        form = forms.ChangeEmailForm(Fred, formdata=data, meta={"csrf": False})

        assert form.validate_on_submit()

    @pytest.mark.parametrize(
        "formdata",
        [
            {"old_email": "notanemail"},
            {"old_email": ""},
            {"new_email": "notanemail", "confirm_new_email": "notanemail"},
            {"new_email": ""},
            {"new_email": "not@the.same"},
            {"confirm_new_email": ""},
        ],
    )
    def test_invalid_inputs(self, Fred, formdata):
        data = {
            "submit": True,
            "old_email": Fred.email,
            "new_email": "totally@real.email",
            "confirm_new_email": "totally@real.email",
        }
        data.update(formdata)
        form = forms.ChangeEmailForm(
            Fred, formdata=MultiDict(data), meta={"csrf": False}
        )

        assert not form.validate_on_submit()


class TestChangePasswordForm(object):
    def test_transforms_to_expected_change_object(self):
        data = MultiDict(
            {
                "old_password": "old_password",
                "new_password": "password",
                "confirm_new_password": "password",
                "submit": True,
            }
        )
        form = forms.ChangePasswordForm(formdata=data)
        expected = PasswordUpdate(old_password="old_password", new_password="password")
        assert form.as_change() == expected

    def test_valid_inputs(self):
        data = MultiDict(
            {
                "submit": True,
                "old_password": "old_password",
                "new_password": "password",
                "confirm_new_password": "password",
            }
        )
        form = forms.ChangePasswordForm(formdata=data, meta={"csrf": False})
        assert form.validate_on_submit()

    @pytest.mark.parametrize(
        "formdata",
        [
            {"old_password": ""},
            {"new_password": ""},
            {"confirm_new_password": ""},
            {"new_password": "doesntmatch"},
        ],
    )
    def test_invalid_inputs(self, formdata):
        data = {
            "old_password": "old_password",
            "new_password": "password",
            "confirm_new_password": "password",
            "submit": True,
        }
        data.update(formdata)
        form = forms.ChangePasswordForm(formdata=MultiDict(data))
        assert not form.validate_on_submit()


class TestChangeUserDetailsForm(object):
    def test_transforms_to_expected_change_object(self):
        data = MultiDict(
            dict(
                submit=True,
                birthday="25 06 2000",
                gender="awesome",
                location="here",
                website="http://flaskbb.org",
                avatar="https://totally.real/image.img",
                signature="test often",
                notes="testy mctest face",
            )
        )
        form = forms.ChangeUserDetailsForm(formdata=data)
        expected = UserDetailsChange(
            birthday=date(2000, 6, 25),
            gender="awesome",
            location="here",
            website="http://flaskbb.org",
            avatar="https://totally.real/image.img",
            signature="test often",
            notes="testy mctest face",
        )

        assert form.as_change() == expected

    @pytest.mark.parametrize(
        "formdata",
        [
            {},
            dict(
                birthday="",
                gender="",
                location="",
                website="",
                avatar="",
                signature="",
                notes="",
            ),
        ],
    )
    def test_valid_inputs(self, formdata):
        data = dict(
            submit=True,
            birthday="25 06 2000",
            gender="awesome",
            location="here",
            website="http://flaskbb.org",
            avatar="https://totally.real/image.img",
            signature="test often",
            notes="testy mctest face",
        )
        data.update(formdata)

        form = forms.ChangeUserDetailsForm(
            formdata=MultiDict(data), meta={"csrf": False}
        )

        assert form.validate_on_submit()

    @pytest.mark.parametrize(
        "formdata",
        [{"avatar": "notaurl"}, {"website": "notanemail"}, {"notes": "a" * 5001}],
    )
    def test_invalid_inputs(self, formdata):
        data = dict(
            submit=True,
            birthday="25 06 2000",
            gender="awesome",
            location="here",
            website="http://flaskbb.org",
            avatar="https://totally.real/image.img",
            signature="test often",
            notes="testy mctest face",
        )
        data.update(formdata)
        form = forms.ChangeUserDetailsForm(
            formdata=MultiDict(data), meta={"csrf": False}
        )

        assert not form.validate_on_submit()
