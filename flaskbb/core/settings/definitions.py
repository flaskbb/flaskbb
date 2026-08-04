"""
flaskbb.core.settings.definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This modules holds the Type definitions for the settings.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, override

from wtforms import fields as wtf_fields
from wtforms import validators as wtf_validators


@dataclass(frozen=True)
class SettingDefinition:
    """Base class for a single setting. Not used directly - use one of
    the value_type-specific subclasses below (IntSetting, BoolSetting, ...).
    """

    key: str  # UPPER_CASE, unique across FlaskBB + plugins
    value: Any  # default value
    name: str
    description: str

    def wtf_field(self):  # pyright: ignore[reportUnknownParameterType]
        """Return a WTForms field instance for this setting."""
        raise NotImplementedError

    def serialize(self, value: Any) -> str:
        """How this setting's value is stored in the DB (JSON, not pickle)."""
        return json.dumps(value)

    def deserialize(self, raw: str) -> Any:
        return json.loads(raw)


@dataclass(frozen=True)
class IntSetting(SettingDefinition):
    min: int | None = None
    max: int | None = None

    @override
    def wtf_field(self):
        validators = []
        if self.min is not None or self.max is not None:
            validators.append(wtf_validators.NumberRange(min=self.min, max=self.max))
        return wtf_fields.IntegerField(
            self.name,
            description=self.description,
            validators=validators,
            default=self.value,
        )


@dataclass(frozen=True)
class BoolSetting(SettingDefinition):
    @override
    def wtf_field(self):
        return wtf_fields.BooleanField(
            self.name, description=self.description, default=self.value
        )


@dataclass(frozen=True)
class StringSetting(SettingDefinition):
    min: int | None = None
    max: int | None = None

    @override
    def wtf_field(self):
        validators = []
        if self.min is not None or self.max is not None:
            validators.append(
                wtf_validators.Length(min=self.min or 0, max=self.max or -1)
            )
        return wtf_fields.StringField(
            self.name,
            description=self.description,
            validators=validators,
            default=self.value,
        )


@dataclass(frozen=True)
class SelectSetting(SettingDefinition):
    choices: Callable[[], list[tuple[Any, str]]] = field()
    coerce: type = str

    @override
    def wtf_field(self):
        return wtf_fields.SelectField(
            self.name,
            description=self.description,
            choices=self.choices(),
            coerce=self.coerce,
            default=self.value,
        )


@dataclass(frozen=True)
class SelectMultipleSetting(SelectSetting):
    @override
    def wtf_field(self):
        return wtf_fields.SelectMultipleField(
            self.name,
            description=self.description,
            choices=self.choices(),
            coerce=self.coerce,
            default=self.value,
        )

    @override
    def serialize(self, value):
        return json.dumps(list(value))


@dataclass(frozen=True)
class SettingGroup:
    key: str
    name: str
    description: str
    settings: tuple[SettingDefinition, ...]
