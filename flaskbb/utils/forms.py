# -*- coding: utf-8 -*-
"""
    flaskbb.utils.forms
    ~~~~~~~~~~~~~~~~~~~

    This module contains stuff for forms.

    :copyright: (c) 2017 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from wtforms import (TextField, IntegerField, FloatField, BooleanField,
                     SelectField, SelectMultipleField, validators)
from flask_wtf import FlaskForm
from flaskbb._compat import text_type, iteritems
from enum import Enum


class FlaskBBForm(FlaskForm):
    def populate_errors(self, errors):
        for (attribute, reason) in errors:
            self.errors.setdefault(attribute, []).append(reason)
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
    for key, value in iteritems(settings):
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
    for key, value in iteritems(settings):
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

        if setting.value_type in {SettingValueType.integer,
                                  SettingValueType.float}:
            validator_class = validators.NumberRange
        elif setting.value_type == SettingValueType.string:
            validator_class = validators.Length

        # generate the validators
        if "min" in setting.extra:
            # Min number validator
            field_validators.append(
                validator_class(min=setting.extra["min"])
            )

        if "max" in setting.extra:
            # Max number validator
            field_validators.append(
                validator_class(max=setting.extra["max"])
            )

        # Generate the fields based on value_type
        # IntegerField
        if setting.value_type == SettingValueType.integer:
            setattr(
                SettingsForm, setting.key,
                IntegerField(setting.name, validators=field_validators,
                             description=setting.description)
            )
        # FloatField
        elif setting.value_type == SettingValueType.float:
            setattr(
                SettingsForm, setting.key,
                FloatField(setting.name, validators=field_validators,
                           description=setting.description)
            )

        # TextField
        elif setting.value_type == SettingValueType.string:
            setattr(
                SettingsForm, setting.key,
                TextField(setting.name, validators=field_validators,
                          description=setting.description)
            )

        # SelectMultipleField
        elif setting.value_type == SettingValueType.selectmultiple:
            # if no coerce is found, it will fallback to unicode
            if "coerce" in setting.extra:
                coerce_to = setting.extra['coerce']
            else:
                coerce_to = text_type

            setattr(
                SettingsForm, setting.key,
                SelectMultipleField(
                    setting.name,
                    choices=setting.extra['choices'](),
                    coerce=coerce_to,
                    description=setting.description
                )
            )

        # SelectField
        elif setting.value_type == SettingValueType.select:
            # if no coerce is found, it will fallback to unicode
            if "coerce" in setting.extra:
                coerce_to = setting.extra['coerce']
            else:
                coerce_to = text_type

            setattr(
                SettingsForm, setting.key,
                SelectField(
                    setting.name,
                    coerce=coerce_to,
                    choices=setting.extra['choices'](),
                    description=setting.description)
            )

        # BooleanField
        elif setting.value_type == SettingValueType.boolean:
            setattr(
                SettingsForm, setting.key,
                BooleanField(setting.name, description=setting.description)
            )

    return SettingsForm
