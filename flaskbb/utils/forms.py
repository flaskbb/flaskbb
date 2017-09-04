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
from flaskbb._compat import text_type


def generate_settings_form(settings):
    """Generates a settings form which includes field validation
    based on our Setting Schema."""
    class SettingsForm(FlaskForm):
        pass

    # now parse the settings in this group
    for setting in settings:
        field_validators = []

        if setting.value_type in ("integer", "float"):
            validator_class = validators.NumberRange
        elif setting.value_type == "string":
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
        if setting.value_type == "integer":
            setattr(
                SettingsForm, setting.key,
                IntegerField(setting.name, validators=field_validators,
                             description=setting.description)
            )
        # FloatField
        elif setting.value_type == "float":
            setattr(
                SettingsForm, setting.key,
                FloatField(setting.name, validators=field_validators,
                           description=setting.description)
            )

        # TextField
        elif setting.value_type == "string":
            setattr(
                SettingsForm, setting.key,
                TextField(setting.name, validators=field_validators,
                          description=setting.description)
            )

        # SelectMultipleField
        elif setting.value_type == "selectmultiple":
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
        elif setting.value_type == "select":
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
        elif setting.value_type == "boolean":
            setattr(
                SettingsForm, setting.key,
                BooleanField(setting.name, description=setting.description)
            )

    return SettingsForm
