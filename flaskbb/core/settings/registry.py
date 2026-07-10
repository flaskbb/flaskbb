# -*- coding: utf-8 -*-
"""
flaskbb.core.settings.registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Central registry that FlaskBB and plugins register setting groups
into. Populated via the flaskbb_load_setting_groups pluggy hook.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections.abc import Sequence
from typing import Callable

from flaskbb.plugins.manager import FlaskBBPluginManager

from .definitions import SettingDefinition, SettingGroup


class SettingsRegistry:
    def __init__(self):
        self._groups: dict[str, SettingGroup] = {}
        self._definitions: dict[str, SettingDefinition] = {}
        self._plugin_group_keys: set[str] = set()

    def register_group(self, group: SettingGroup, *, is_plugin: bool = False) -> None:
        if group.key in self._groups:
            raise ValueError(f"Duplicate setting group: {group.key}")

        for setting in group.settings:
            normalized_key = setting.key.upper()
            if normalized_key in self._definitions:
                raise ValueError(f"Duplicate setting key: {setting.key}")

        self._groups[group.key] = group
        for setting in group.settings:
            self._definitions[setting.key.upper()] = setting
        if is_plugin:
            self._plugin_group_keys.add(group.key)

    def group(self, key: str) -> SettingGroup:
        return self._groups[key]

    def all_groups(self):
        return self._groups.values()

    def core_groups(self):
        """Groups loaded via flaskbb_load_internal_setting_groups"""
        return [g for k, g in self._groups.items() if k not in self._plugin_group_keys]

    def plugin_groups(self):
        """Groups loaded via flaskbb_load_setting_groups"""
        return [g for k, g in self._groups.items() if k in self._plugin_group_keys]

    def is_plugin_group(self, key: str) -> bool:
        return key in self._plugin_group_keys

    def definition(self, key: str) -> SettingDefinition:
        # normalize so a lower/mixed-case key (e.g. a legacy DB row that
        # wasn't migrated) still resolves against the UPPER_CASE keys
        # every SettingDefinition is registered under
        return self._definitions[key.upper()]

    def all_definitions(self):
        return self._definitions.values()

    def _load(
        self,
        hook_caller: Callable[
            [], Sequence[SettingGroup] | Sequence[Sequence[SettingGroup]]
        ],
        *,
        is_plugin: bool,
    ) -> None:
        results = hook_caller()
        for result in results:
            groups: Sequence[SettingGroup] = (
                result if isinstance(result, (list, tuple, Sequence)) else (result,)
            )
            for group in groups:
                self.register_group(group, is_plugin=is_plugin)

    def load_from_internal(self, plugin_manager: FlaskBBPluginManager) -> None:
        """Call flaskbb_load_internal_setting_groups - core's own hook.
        Only FlaskBB's own hookimpls should implement this one."""
        self._load(
            plugin_manager.hook.flaskbb_load_internal_setting_groups,
            is_plugin=False,
        )

    def load_from_plugins(self, plugin_manager: FlaskBBPluginManager) -> None:
        """Call flaskbb_load_setting_groups - the public hook that
        third-party plugins implement for their own SettingGroups.

        Implementations may return a single SettingGroup or a list of
        them (mirrors the flaskbb_load_post_markdown_class convention of
        collecting-and-composing hook results rather than calling
        register_group directly from plugin code).
        """
        self._load(plugin_manager.hook.flaskbb_load_setting_groups, is_plugin=True)


# Singleton used throughout the app
setting_registry = SettingsRegistry()
