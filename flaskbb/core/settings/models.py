"""
The Setting model. Owns both storage and caching for settings values.

`value` is stored as JSON text instead of PickleType - avoids arbitrary
code execution risk from unpickling, and every setting value type (int,
bool, str, list[str]) is JSON-safe anyway.
"""

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Mapped, mapped_column

from flaskbb.extensions import cache, db

from .definitions import SettingDefinition
from .registry import setting_registry


class Setting(db.Model):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(db.String(255), primary_key=True)
    value: Mapped[str | None] = mapped_column(db.Text)  # JSON-encoded
    group_key: Mapped[str] = mapped_column(db.String(255), index=True)

    def __init__(self, key: str, value: str | None, group_key: str):
        pass

    def get_value(self, definition: SettingDefinition):
        if self.value is None:
            return None
        return definition.deserialize(self.value)

    def set_value(self, definition: SettingDefinition, value: Any) -> None:
        self.value = definition.serialize(value)

    @classmethod
    @cache.cached(key_prefix="settings")
    def as_dict(cls) -> dict[str, Any]:
        """Load and deserialize every setting value from the DB."""
        rows = db.session.execute(select(cls)).scalars().all()
        return {
            row.key: None
            if row.value is None
            else setting_registry.definition(row.key).deserialize(row.value)
            for row in rows
        }

    @classmethod
    def invalidate_cache(cls) -> None:
        """Invalidates the cached settings dict."""
        cache.delete_memoized(cls.as_dict, cls)

    @classmethod
    def update(cls, group_key: str, form_data: dict[str, Any]) -> None:
        """Save a settings group's form data to the DB and invalidate
        the cache in one step.

        :param group_key: the SettingGroup.key whose settings are being
            saved (e.g. "general").
        :param form_data: dict of {setting_key: new_value}, typically
            form.data from the WTForm built via build_form(group).
        """
        group = setting_registry.group(group_key)
        for setting_def in group.settings:
            row = db.session.execute(
                select(cls).where(cls.key == setting_def.key)
            ).scalar_one()
            row.set_value(setting_def, form_data[setting_def.key])

        db.session.commit()
        cls.invalidate_cache()

    @classmethod
    def install_group(cls, group_key: str) -> None:
        """Insert DB rows (using each definition's default value) for
        any setting in this group that doesn't have one yet.

        Used when a plugin is installed for the first time, or when a
        new setting is added to an existing group via a fixture/plugin
        update.
        """
        group = setting_registry.group(group_key)
        existing_keys = set(
            db.session.execute(
                select(cls.key).where(cls.key.in_([s.key for s in group.settings]))
            ).scalars()
        )
        for setting_def in group.settings:
            if setting_def.key not in existing_keys:
                db.session.add(
                    cls(
                        key=setting_def.key,
                        value=setting_def.serialize(setting_def.value),
                        group_key=group_key,
                    )
                )
        db.session.commit()
        cls.invalidate_cache()

    @classmethod
    def remove_group(cls, group_key: str) -> None:
        """Delete every DB row belonging to a settings group and
        invalidate the cache in one step.

        Used when uninstalling a plugin - deletes only rows tagged with
        this group_key, so other groups settings are untouched.
        """
        db.session.execute(delete(cls).where(cls.group_key == group_key))
        db.session.commit()
        cls.invalidate_cache()
