"""
flaskbb.utils.forms
~~~~~~~~~~~~~~~~~~~

This module contains stuff for forms.

:copyright: (c) 2017 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import functools
from collections.abc import Callable
from typing import override, TypeVar

from flask import current_app
from flask_babelplus import lazy_gettext as _
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileAllowed, FileSize
from wtforms import Field, Form

from flaskbb.extensions import limiter
from flaskbb.utils.settings import flaskbb_config

_F = TypeVar("_F", bound="FlaskForm")


def add_recaptcha_field(
    only_on_ratelimit: bool = False,
) -> Callable[[type[_F]], Callable[[], _F]]:
    def decorator(cls: type[_F]) -> Callable[[], _F]:
        @functools.wraps(cls)
        def decorated_class() -> _F:
            from flaskbb.core.settings import flaskbb_config
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
    def __call__(self, form: Form, field: Field) -> None:
        self.upload_set = current_app.config.get("AVATAR_EXTENSIONS", [])  # pyright: ignore[reportUnknownMemberType]
        return super().__call__(form, field)  # pyright: ignore[reportUnknownMemberType]


class AvatarSizeValidator(FileSize):
    def __init__(self, message: str | None = None):
        super().__init__(max_size=None, min_size=0, message=message)  # pyright: ignore[reportUnknownMemberType]

    @override
    def __call__(self, form: Form, field: Field) -> None:
        self.max_size = flaskbb_config["AVATAR_SIZE"] * 1024
        self.min_size = 0
        if not self.message:
            self.message = "Image is too big! {}kb are allowed.".format(
                flaskbb_config["AVATAR_SIZE"]
            )
        return super().__call__(form, field)  # pyright: ignore[reportUnknownMemberType]
