"""
Central registry that FlaskBB and plugins register setting groups
into. Populated via the flaskbb_load_setting_groups pluggy hook.
"""

from collections.abc import Sequence

from flaskbb.plugins.manager import FlaskBBPluginManager

from .definitions import SettingDefinition, SettingGroup


class SettingsRegistry:
    def __init__(self):
        self._groups: dict[str, SettingGroup] = {}
        self._definitions: dict[str, SettingDefinition] = {}

    def register_group(self, group: SettingGroup) -> None:
        if group.key in self._groups:
            raise ValueError(f"Duplicate setting group: {group.key}")

        for setting in group.settings:
            if setting.key in self._definitions:
                raise ValueError(f"Duplicate setting key: {setting.key}")

        self._groups[group.key] = group
        for setting in group.settings:
            self._definitions[setting.key] = setting

    def group(self, key: str) -> SettingGroup:
        return self._groups[key]

    def all_groups(self):
        return self._groups.values()

    def definition(self, key: str) -> SettingDefinition:
        return self._definitions[key]

    def all_definitions(self):
        return self._definitions.values()

    def load_from_internal(self, plugin_manager: FlaskBBPluginManager) -> None:
        """Call the flaskbb_load_setting_groups hook and register every
        SettingGroup returned by core and by any installed plugin.

        Implementations may return a single SettingGroup or a list of
        them (mirrors the flaskbb_load_post_markdown_class convention of
        collecting-and-composing hook results rather than calling
        register_group directly from plugin code).
        """
        results: Sequence[SettingGroup] | Sequence[Sequence[SettingGroup]] = (
            plugin_manager.hook.flaskbb_internal_setting_groups()
        )
        for result in results:
            groups: Sequence[SettingGroup] = (
                result if isinstance(result, (list, tuple, Sequence)) else (result,)
            )
            for group in groups:
                self.register_group(group)

    def load_from_plugins(self, plugin_manager: FlaskBBPluginManager) -> None:
        """Call the flaskbb_load_setting_groups hook and register every
        SettingGroup returned by core and by any installed plugin.

        Implementations may return a single SettingGroup or a list of
        them (mirrors the flaskbb_load_post_markdown_class convention of
        collecting-and-composing hook results rather than calling
        register_group directly from plugin code).
        """
        results: Sequence[SettingGroup] | Sequence[Sequence[SettingGroup]] = (
            plugin_manager.hook.flaskbb_load_setting_groups()
        )
        for result in results:
            groups: Sequence[SettingGroup] = (
                result if isinstance(result, (list, tuple, Sequence)) else (result,)
            )
            for group in groups:
                self.register_group(group)

    def load(self, plugin_manager: FlaskBBPluginManager) -> None:
        pass


# Singleton used throughout the app
setting_registry = SettingsRegistry()
