"""
flaskbb.utils.forms
~~~~~~~~~~~~~~~~~~~

This module contains stuff for forms.

:copyright: (c) 2017 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import functools
import json
from collections.abc import Callable
from typing import Any, override, TypeVar
from urllib import request as http
from urllib.parse import urlencode

from flask_babelplus import lazy_gettext as _
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileSize
from flask_wtf.recaptcha import fields as recaptcha_fields
from flask_wtf.recaptcha import validators as recaptcha_validators
from flask_wtf.recaptcha import widgets as recaptcha_widgets
from markupsafe import Markup
from wtforms import Field, ValidationError
from wtforms.form import BaseForm

from flaskbb.extensions import limiter
from flaskbb.settings import flaskbb_config
from flaskbb.utils.proxies import current_app

_F = TypeVar("_F", bound="FlaskForm")


def recaptcha_key(name: str) -> str:
    """The key saved in the admin settings wins over the config file."""
    key = flaskbb_config.get(name) or current_app.config.get(name)
    if not key:
        raise RuntimeError(f"{name} is set neither in the admin settings nor in the config")
    return key


class RecaptchaWidget(recaptcha_widgets.RecaptchaWidget):
    @override
    def __call__(self, field: Any, error: Any = None, **kwargs: Any) -> Markup:
        kwargs.setdefault("id", field.id)
        return self.recaptcha_html(  # pyright: ignore[reportUnknownMemberType]
            recaptcha_key("RECAPTCHA_PUBLIC_KEY"), nonce=field.nonce, **kwargs
        )


class Recaptcha(recaptcha_validators.Recaptcha):
    @override
    def _validate_recaptcha(self, response: str, remote_addr: str | None) -> bool:
        verify_server = (
            current_app.config.get("RECAPTCHA_VERIFY_SERVER")
            or recaptcha_validators.RECAPTCHA_VERIFY_SERVER_DEFAULT
        )
        data = urlencode(
            {
                "secret": recaptcha_key("RECAPTCHA_PRIVATE_KEY"),
                "remoteip": remote_addr,
                "response": response,
            }
        )
        http_response = http.urlopen(verify_server, data.encode("utf-8"))
        if http_response.code != 200:
            return False

        json_resp = json.loads(http_response.read())
        if json_resp["success"]:
            return True

        for error in json_resp.get("error-codes", []):
            if error in recaptcha_validators.RECAPTCHA_ERROR_CODES:
                raise ValidationError(recaptcha_validators.RECAPTCHA_ERROR_CODES[error])
        return False


class RecaptchaField(recaptcha_fields.RecaptchaField):
    widget = RecaptchaWidget()

    def __init__(self, label: str = "", validators: Any = None, nonce: Any = None, **kwargs: Any):
        super().__init__(label, validators or [Recaptcha()], nonce, **kwargs)  # pyright: ignore[reportUnknownMemberType]


def add_recaptcha_field(
    only_on_ratelimit: bool = False,
) -> Callable[[type[_F]], Callable[[], _F]]:
    def decorator(cls: type[_F]) -> Callable[[], _F]:
        @functools.wraps(cls)
        def decorated_class() -> _F:
            from flaskbb.utils.helpers import enforce_recaptcha

            if flaskbb_config["RECAPTCHA_ENABLED"]:
                if not only_on_ratelimit or only_on_ratelimit and enforce_recaptcha(limiter):

                    class RecaptchaEnabledForm(cls):  # type: ignore[valid-type,misc]
                        recaptcha = RecaptchaField(_("Captcha"))

                    return RecaptchaEnabledForm()  # pyright: ignore
            return cls()

        return decorated_class  # pyright: ignore[reportUnknownVariableType]

    return decorator


class AvatarExtensionValidator(FileAllowed):
    def __init__(self, message: str | None = None):
        super().__init__(upload_set=[], message=message)  # pyright: ignore[reportUnknownMemberType]

    @override
    def __call__(self, form: BaseForm, field: Field) -> None:
        self.upload_set = current_app.config.get("AVATAR_EXTENSIONS", [])
        return super().__call__(form, field)  # pyright: ignore[reportUnknownMemberType]


class AvatarSizeValidator(FileSize):
    def __init__(self, message: str | None = None):
        super().__init__(max_size=0, min_size=0, message=message)  # pyright: ignore[reportUnknownMemberType]

    @override
    def __call__(self, form: BaseForm, field: Field) -> None:
        self.max_size = flaskbb_config["AVATAR_SIZE"] * 1024
        self.min_size = 0
        if not self.message:
            self.message = "Image is too big! {}kb are allowed.".format(
                flaskbb_config["AVATAR_SIZE"]
            )
        return super().__call__(form, field)  # pyright: ignore[reportUnknownMemberType]
