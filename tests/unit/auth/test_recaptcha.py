from io import BytesIO
from types import SimpleNamespace

import pytest
from flask_wtf import FlaskForm
from flaskbb.settings import flaskbb_config
from flaskbb.utils import validators
from flaskbb.utils.validators import Recaptcha, recaptcha_key, RecaptchaField

pytestmark = pytest.mark.usefixtures("default_settings")


class CaptchaForm(FlaskForm):
    recaptcha = RecaptchaField()


def test_the_admin_setting_wins_over_the_config(request_context, application, monkeypatch):
    monkeypatch.setitem(application.config, "RECAPTCHA_PUBLIC_KEY", "config-site-key")
    flaskbb_config["RECAPTCHA_PUBLIC_KEY"] = "admin-site-key"

    assert recaptcha_key("RECAPTCHA_PUBLIC_KEY") == "admin-site-key"


def test_the_config_is_used_while_the_admin_setting_is_empty(
    request_context, application, monkeypatch
):
    monkeypatch.setitem(application.config, "RECAPTCHA_PUBLIC_KEY", "config-site-key")
    flaskbb_config["RECAPTCHA_PUBLIC_KEY"] = ""

    assert recaptcha_key("RECAPTCHA_PUBLIC_KEY") == "config-site-key"


def test_a_missing_key_is_reported(request_context, application, monkeypatch):
    monkeypatch.delitem(application.config, "RECAPTCHA_PRIVATE_KEY", raising=False)
    flaskbb_config["RECAPTCHA_PRIVATE_KEY"] = ""

    with pytest.raises(RuntimeError, match="RECAPTCHA_PRIVATE_KEY"):
        recaptcha_key("RECAPTCHA_PRIVATE_KEY")


def test_the_widget_renders_the_site_key_from_the_admin_settings(request_context):
    flaskbb_config["RECAPTCHA_PUBLIC_KEY"] = "admin-site-key"
    form = CaptchaForm(meta={"csrf": False})

    assert 'data-sitekey="admin-site-key"' in str(form.recaptcha)


def test_the_validator_verifies_with_the_secret_from_the_admin_settings(
    request_context, monkeypatch
):
    flaskbb_config["RECAPTCHA_PRIVATE_KEY"] = "admin-secret-key"
    requests = []

    def urlopen(url, data):
        requests.append((url, data))
        return SimpleNamespace(code=200, read=BytesIO(b'{"success": true}').read)

    monkeypatch.setattr(validators.http, "urlopen", urlopen)

    assert Recaptcha()._validate_recaptcha("the-token", "127.0.0.1") is True
    assert requests == [
        (
            "https://www.google.com/recaptcha/api/siteverify",
            b"secret=admin-secret-key&remoteip=127.0.0.1&response=the-token",
        )
    ]
