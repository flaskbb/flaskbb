"""
Auto-generates a Flask-WTF form class for a given SettingGroup
"""

from typing import Any

from flask_wtf import FlaskForm

from .definitions import SettingGroup


def build_form(group: SettingGroup) -> type[FlaskForm]:
    """Dynamically create a FlaskForm subclass with one field per setting
    in the group. Field keys stay UPPER_CASE to match the setting keys.
    """
    attrs = {setting.key: setting.wtf_field() for setting in group.settings}  # pyright: ignore[reportUnknownVariableType]
    class_name = f"{group.key.title().replace('_', '')}SettingsForm"
    return type(class_name, (FlaskForm,), attrs)  # pyright: ignore[reportUnknownArgumentType]


def populate_form(group: SettingGroup, current_values: dict[Any, Any]) -> FlaskForm:
    """Build the form for a group and populate it with current DB values."""
    form_cls = build_form(group)
    form = form_cls(data=current_values)
    return form
