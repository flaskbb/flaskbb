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

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from flaskbb.extensions import BaseModel, cache, db

from .definitions import SettingDefinition
from .registry import setting_registry

# Fields Flask-WTF/WTForms inject into form.data that are never actual
# settings - excluded by default in Setting.update() so callers don't
# have to strip them manually on every call site.
DEFAULT_EXCLUDED_FORM_KEYS = frozenset({"csrf_token"})

_SETTINGS_CACHE_KEY = "settings"


def display_key(group_key: str, definition_key: str) -> str:
    """The publicly exposed key for core settings (without GROUPKEY_, e.q. PROJECT_TITLE)
    and GROUPKEY_KEY-prefixed for plugin settings (PORTAL_FORUM_IDS).
    """
    if setting_registry.is_plugin_group(group_key):
        return f"{group_key.upper()}_{definition_key}"
    return definition_key


@dataclass(frozen=True)
class SettingsDiff:
    """A settings diff of a group's registered SettingDefinitions
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


class Setting(BaseModel):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(sa.String(255), primary_key=True, nullable=False)
    value: Mapped[str | None] = mapped_column(sa.Text)  # JSON-encoded
    group_key: Mapped[str] = mapped_column(sa.String(255), index=True)

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

    @staticmethod
    @cache.cached(key_prefix=_SETTINGS_CACHE_KEY)
    def as_dict() -> dict[str, Any]:
        """Load and deserialize every setting value from the DB.

        Core settings stay unprefixed (settings.PROJECT_TITLE),
        plugin settings are exposed prefixed with
        their group_key (settings.PORTAL_FORUM_IDS).
        """
        settings = db.session.execute(sa.select(Setting)).scalars().all()
        config: dict[str, Any] = {}

        for s in settings:
            try:
                definition = setting_registry.definition(s.group_key, s.key)
            except KeyError:
                continue

            exposed_key = display_key(s.group_key, definition.key)
            config[exposed_key] = definition.deserialize(s.value) if s.value else None
        return config

    @classmethod
    def invalidate_cache(cls):
        """Invalidates this objects cached metadata."""
        cache.delete(_SETTINGS_CACHE_KEY)

    @classmethod
    def update(
        cls,
        group_key: str,
        settings: dict[str, Any],
        *,
        exclude: Iterable[str] = DEFAULT_EXCLUDED_FORM_KEYS,
    ) -> None:
        """Save a settings group's form data to the DB and invalidate
        the cache in one step.

        :param group_key: the SettingGroup.key whose settings are being
            saved (e.g. "general", "portal"). Required because
            (group_key, key) together identify a setting.
        :param settings: dict of {setting_key: new_value}, typically
            form.data from the WTForm built via build_form(group)
        :param exclude: keys to skip.
            Defaults to just "csrf_token" because forms usually contain this key.
        """
        excluded_keys = {key.lower() for key in exclude}
        rows = {
            row.key.lower(): row
            for row in db.session.execute(
                sa.select(cls).where(cls.group_key == group_key)
            ).scalars()
        }
        for key, value in settings.items():
            if key.lower() in excluded_keys:
                continue

            definition = setting_registry.definition(group_key, key)
            rows[definition.key.lower()].set_value(definition, value)

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
                sa.select(sa.func.lower(cls.key)).where(cls.group_key == group_key)
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
            sa.select(cls).where(cls.group_key == group_key)
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
                sa.select(sa.func.lower(cls.key)).where(
                    cls.group_key == group_key,
                    sa.func.lower(cls.key).in_(group_setting_keys),
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
        db.session.execute(sa.delete(cls).where(cls.group_key == group_key))
        db.session.commit()
        cls.invalidate_cache()
