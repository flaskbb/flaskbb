"""
flaskbb.permissions.registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Central registry that FlaskBB and plugins register permission groups
into. Populated via the flaskbb_load_internal_permissions and
flaskbb_load_permissions pluggy hooks.

:copyright: (c) 2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections.abc import Callable, Sequence

from flaskbb.plugins.manager import FlaskBBPluginManager

from .definitions import PermissionDefinition, PermissionGroup


class PermissionsRegistry:
    def __init__(self):
        self._groups: dict[str, PermissionGroup] = {}
        # keyed by the stored key: the raw key for FlaskBB's own permissions,
        # "<group key>_<raw key>" for a plugin's
        self._definitions: dict[str, PermissionDefinition] = {}
        self._plugin_group_keys: set[str] = set()

    def register_group(self, group: PermissionGroup, *, is_plugin: bool = False) -> None:
        if group.key in self._groups:
            raise ValueError(f"Duplicate permission group: {group.key}")

        prefix = f"{group.key}_" if is_plugin else ""
        for permission in group.permissions:
            if prefix + permission.key in self._definitions:
                raise ValueError(f"Duplicate permission: {prefix + permission.key}")

        self._groups[group.key] = group
        for permission in group.permissions:
            self._definitions[prefix + permission.key] = permission
        if is_plugin:
            self._plugin_group_keys.add(group.key)

    def unregister_group(self, key: str) -> None:
        group = self._groups.pop(key)
        prefix = f"{key}_" if key in self._plugin_group_keys else ""
        for permission in group.permissions:
            del self._definitions[prefix + permission.key]
        self._plugin_group_keys.discard(key)

    def keys(self) -> list[str]:
        """The stored keys of every registered permission, in registration order."""
        return list(self._definitions)

    def is_registered(self, key: str) -> bool:
        return key in self._definitions

    def definition(self, key: str) -> PermissionDefinition:
        return self._definitions[key]

    def defaults(self) -> dict[str, bool]:
        return {key: definition.default for key, definition in self._definitions.items()}

    def sections(self) -> list[tuple[PermissionGroup, list[tuple[str, PermissionDefinition]]]]:
        """Every group with its permissions as (stored key, definition) pairs."""
        sections: list[tuple[PermissionGroup, list[tuple[str, PermissionDefinition]]]] = []
        for group in self._groups.values():
            prefix = f"{group.key}_" if group.key in self._plugin_group_keys else ""
            sections.append(
                (group, [(prefix + permission.key, permission) for permission in group.permissions])
            )
        return sections

    def _load(
        self,
        hook_caller: Callable[[], Sequence[PermissionGroup] | Sequence[Sequence[PermissionGroup]]],
        *,
        is_plugin: bool,
    ) -> None:
        for result in hook_caller():
            groups: Sequence[PermissionGroup] = (
                result if isinstance(result, Sequence) else (result,)
            )
            for group in groups:
                self.register_group(group, is_plugin=is_plugin)

    def load_from_internal(self, plugin_manager: FlaskBBPluginManager) -> None:
        """Calls flaskbb_load_internal_permissions - FlaskBB's own hook."""
        self._load(plugin_manager.hook.flaskbb_load_internal_permissions, is_plugin=False)

    def load_from_plugins(self, plugin_manager: FlaskBBPluginManager) -> None:
        """Calls flaskbb_load_permissions - the public hook plugins implement."""
        self._load(plugin_manager.hook.flaskbb_load_permissions, is_plugin=True)


# Singleton used throughout the app
permission_registry = PermissionsRegistry()
