# -*- coding: utf-8 -*-
"""
flaskbb.utils.forms
~~~~~~~~~~~~~~~~~~~

This module contains stuff for forms.

:copyright: (c) 2017 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import functools
from collections.abc import Iterable
from enum import Enum
from typing import Any, TypeVar, override

from flask_babelplus import lazy_gettext as _
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    StringField,
    validators,
)

from flaskbb.extensions import limiter

_F = TypeVar("_F", bound="FlaskBBForm")


def add_recaptcha_field(only_on_ratelimit: bool = False):
    def decorator(cls: type[_F]):
        @functools.wraps(cls)
        def decorated_class(*args: Any, **kwargs: Any) -> _F:
            from flaskbb.utils.helpers import enforce_recaptcha
            from flaskbb.utils.settings import flaskbb_config

            if flaskbb_config["RECAPTCHA_ENABLED"]:
                if (
                    not only_on_ratelimit
                    or only_on_ratelimit
                    and enforce_recaptcha(limiter)
                ):

                    class RecaptchaEnabledForm(cls):
                        recaptcha = RecaptchaField(_("Captcha"))

                    return RecaptchaEnabledForm()  # pyright: ignore
            return cls()

        return decorated_class

    return decorator


class FlaskBBForm(FlaskForm):
    @override
    def populate_obj(self, obj, exclude: Iterable[str] | None = None):
        """Populates the attributes of the passed `obj` with data from the
        form's fields, skipping any field names listed in `exclude`.

        :param obj: The object to populate.
        :param exclude: An iterable of field names to skip.
        """
        exclude = exclude or ()
        for name, field in self._fields.items():
            if name not in exclude:
                field.populate_obj(obj, name)

    def populate_errors(self, errors: list[tuple[str, str]]):
        for attribute, reason in errors:
            self.errors.setdefault(attribute, []).append(reason)  # pyright: ignore
            field = getattr(self, attribute, None)
            if field:
                field.errors.append(reason)


class SettingValueType(Enum):
    string = 0
    integer = 1
    float = 3
    boolean = 4
    select = 5
    selectmultiple = 6


def populate_settings_dict(form, settings):
    new_settings = {}
    for key, value in settings.items():
        try:
            # check if the value has changed
            if value == form[key].data:
                continue
            else:
                new_settings[key] = form[key].data
        except KeyError:
            pass

    return new_settings


def populate_settings_form(form, settings):
    for key, value in settings.items():
        try:
            form[key].data = value
        except (KeyError, ValueError):
            pass

    return form


# TODO(anr): clean this up
def generate_settings_form(settings):  # noqa: C901
    """Generates a settings form which includes field validation
    based on our Setting Schema."""

    class SettingsForm(FlaskBBForm):
        pass

    # now parse the settings in this group
    for setting in settings:
        field_validators = []

        if setting.value_type in {SettingValueType.integer, SettingValueType.float}:
            validator_class = validators.NumberRange
        elif setting.value_type == SettingValueType.string:
            validator_class = validators.Length

        # generate the validators
        if "min" in setting.extra:
            # Min number validator
            field_validators.append(validator_class(min=setting.extra["min"]))

        if "max" in setting.extra:
            # Max number validator
            field_validators.append(validator_class(max=setting.extra["max"]))

        # Generate the fields based on value_type
        # IntegerField
        if setting.value_type == SettingValueType.integer:
            setattr(
                SettingsForm,
                setting.key,
                IntegerField(
                    setting.name,
                    validators=field_validators,
                    description=setting.description,
                ),
            )
        # FloatField
        elif setting.value_type == SettingValueType.float:
            setattr(
                SettingsForm,
                setting.key,
                FloatField(
                    setting.name,
                    validators=field_validators,
                    description=setting.description,
                ),
            )

        # StringField
        elif setting.value_type == SettingValueType.string:
            setattr(
                SettingsForm,
                setting.key,
                StringField(
                    setting.name,
                    validators=field_validators,
                    description=setting.description,
                ),
            )

        # SelectMultipleField
        elif setting.value_type == SettingValueType.selectmultiple:
            # if no coerce is found, it will fallback to unicode
            if "coerce" in setting.extra:
                coerce_to = setting.extra["coerce"]
            else:
                coerce_to = str

            setattr(
                SettingsForm,
                setting.key,
                SelectMultipleField(
                    setting.name,
                    choices=setting.extra["choices"](),
                    coerce=coerce_to,
                    description=setting.description,
                ),
            )

        # SelectField
        elif setting.value_type == SettingValueType.select:
            # if no coerce is found, it will fallback to unicode
            if "coerce" in setting.extra:
                coerce_to = setting.extra["coerce"]
            else:
                coerce_to = str

            setattr(
                SettingsForm,
                setting.key,
                SelectField(
                    setting.name,
                    coerce=coerce_to,
                    choices=setting.extra["choices"](),
                    description=setting.description,
                ),
            )

        # BooleanField
        elif setting.value_type == SettingValueType.boolean:
            setattr(
                SettingsForm,
                setting.key,
                BooleanField(setting.name, description=setting.description),
            )

    return SettingsForm
