# -*- coding: utf-8 -*-
"""
flaskbb.core.settings.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the Setting model. It owns both storage and caching for
settings values.

`value` is stored as JSON text instead of PickleType - avoids arbitrary
code execution risk from unpickling, and every setting value type (int,
bool, str, list[str]) is JSON-safe anyway.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Mapped, mapped_column

from flaskbb.extensions import cache, db

from .definitions import SettingDefinition
from .registry import setting_registry


@dataclass(frozen=True)
class SettingsDiff:
    """Read-only comparison of a group's registered SettingDefinitions
    against what actually has rows in the DB. Used to check whether a
    plugin needs a settings upgrade before actually performing one."""

    missing: tuple[str, ...]  # definition keys with no DB row yet
    obsolete: tuple[str, ...]  # DB rows with no matching definition anymore

    @property
    def has_changes(self) -> bool:
        return bool(self.missing or self.obsolete)

    @property
    def log_output(self) -> str:
        return f"new: {', '.join(self.missing)}, obsolete: {', '.join(self.obsolete)}"


class Setting(db.Model):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(db.String(255), primary_key=True, nullable=False)
    value: Mapped[str | None] = mapped_column(db.Text)  # JSON-encoded
    group_key: Mapped[str] = mapped_column(db.String(255), index=True)

    def __init__(self, key: str, value: str | None, group_key: str):
        self.key = key
        self.value = value
        self.group_key = group_key

    def get_value(self, definition: SettingDefinition):
        if self.value is None:
            return None
        return definition.deserialize(self.value)

    def set_value(self, definition: SettingDefinition, value: Any) -> None:
        self.value = definition.serialize(value)

    @classmethod
    @cache.cached(key_prefix="settings")
    def as_dict(cls) -> dict[str, Any]:
        """Load and deserialize every setting value from the DB.

        The setting definitions are the single source of truth: a Setting key-value
        only ends up in the result if it still has a matching
        SettingDefinition. A row with no definition (e.g. a plugin removed
        the setting but its settings haven't been pruned yet) is silently skipped.
        """
        settings = db.session.execute(select(cls)).scalars().all()
        config: dict[str, Any] = {}
        for s in settings:
            try:
                definition = setting_registry.definition(s.key)
            except KeyError:
                continue
            config[definition.key] = (
                definition.deserialize(s.value) if s.value else None
            )
        return config

    @classmethod
    def invalidate_cache(cls):
        """Invalidates this objects cached metadata."""
        cache.delete_memoized(cls.as_dict, cls)

    @classmethod
    def update(cls, settings: dict[str, Any]) -> None:
        """Save one or more settings by key and invalidate the cache in
        one step.

        :param settings: dict of {setting_key: new_value}.
            Each key resolves its own definition (and therefore group) via the
            registry, so the caller doesn't need to know or pass a
            group_key.
        """
        for key, value in settings.items():
            definition = setting_registry.definition(key)
            setting = db.session.execute(
                select(cls).where(func.lower(cls.key) == definition.key.lower())
            ).scalar_one()
            setting.set_value(definition, value)

        db.session.commit()
        cls.invalidate_cache()

    @classmethod
    def diff_group(cls, group_key: str) -> "SettingsDiff":
        """Compares a group's currently registered SettingDefinitions
        against what actually has DB rows tagged with this group_key.

        :returns: SettingsDiff listing which definition keys have no DB
            row yet and which DB rows no longer match any definition .
        """
        group = setting_registry.group(group_key)
        group_setting_keys = {s.key.lower() for s in group.settings}
        existing_keys_lower = set(
            db.session.execute(
                select(func.lower(cls.key)).where(cls.group_key == group_key)
            ).scalars()
        )

        missing = tuple(sorted(group_setting_keys - existing_keys_lower))
        obsolete = tuple(sorted(existing_keys_lower - group_setting_keys))
        return SettingsDiff(missing=missing, obsolete=obsolete)

    @classmethod
    def prune_group(cls, group_key: str) -> None:
        """Removes settings from a group that are no longer used. For example,
        removed from the SettingDefinitions file.
        """
        group = setting_registry.group(group_key)
        group_setting_keys = {s.key.lower() for s in group.settings}
        existing_settings = db.session.execute(
            select(cls).where(cls.group_key == group_key)
        ).scalars()
        for setting in existing_settings:
            if setting.key.lower() not in group_setting_keys:
                db.session.delete(setting)

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
        group_setting_keys = {s.key.lower() for s in group.settings}
        existing_keys_lower = set(
            db.session.execute(
                select(func.lower(cls.key)).where(
                    func.lower(cls.key).in_(group_setting_keys)
                )
            ).scalars()
        )
        for setting_def in group.settings:
            if setting_def.key.lower() not in existing_keys_lower:
                db.session.add(
                    cls(
                        key=setting_def.key,
                        value=setting_def.serialize(setting_def.value),
                        group_key=group.key,
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
