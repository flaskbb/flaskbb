"""
flaskbb.core.settings.registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Central registry that FlaskBB and plugins register setting groups
into. Populated via the flaskbb_load_setting_groups pluggy hook.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections.abc import Callable, Sequence

from flaskbb.plugins.manager import FlaskBBPluginManager

from .definitions import SettingDefinition, SettingGroup


class SettingsRegistry:
    def __init__(self):
        self._groups: dict[str, SettingGroup] = {}
        # keyed by (group_key, KEY.upper()) instead of a flat key - two
        # different groups (core or plugin) can register the same
        # raw setting key without colliding, since uniqueness is scoped
        # to the group rather than global.
        self._definitions: dict[tuple[str, str], SettingDefinition] = {}
        self._plugin_group_keys: set[str] = set()

    def register_group(self, group: SettingGroup, *, is_plugin: bool = False) -> None:
        if group.key in self._groups:
            raise ValueError(f"Duplicate setting group: {group.key}")

        seen: set[str] = set()
        for setting in group.settings:
            normalized = setting.key.upper()
            if normalized in seen:
                raise ValueError(
                    f"Duplicate setting key in group {group.key!r}: {setting.key}"
                )
            seen.add(normalized)

        self._groups[group.key] = group
        for setting in group.settings:
            self._definitions[(group.key, setting.key.upper())] = setting
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

    def definition(self, group_key: str, key: str) -> SettingDefinition:
        return self._definitions[(group_key, key.upper())]

    def all_definitions(self):
        return self._definitions.values()

    def resolve_display_key(self, display_key: str) -> tuple[str, str]:
        """Reverses a GROUPKEY_KEY display key (e.g. "PORTAL_FORUM_IDS")
        back into its (group_key, raw_key) pair (e.g. ("portal", "FORUM_IDS")).

        Raises KeyError if no registered (group_key, key) pair produces
        this display key.
        """
        upper_key = display_key.upper()

        # plugin settings are prefixed with their group_key
        for group_key in sorted(self._plugin_group_keys, key=len, reverse=True):
            prefix = f"{group_key.upper()}_"
            if upper_key.startswith(prefix):
                candidate_key = upper_key[len(prefix) :]
                if (group_key, candidate_key) in self._definitions:
                    return group_key, candidate_key

        # core settings are unprefixed - the display key IS the raw key
        for group_key in self._groups:
            if group_key in self._plugin_group_keys:
                continue
            if (group_key, upper_key) in self._definitions:
                return group_key, upper_key

        raise KeyError(f"No such setting: {display_key!r}")

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
