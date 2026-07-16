"""
A plugin's settings are just a SettingGroup registered via the
flaskbb_load_setting_groups hook keyed by group_key == plugin
name, stored as ordinary Setting rows alongside core's own settings.
"""

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from flaskbb.core.settings.forms import build_form
from flaskbb.core.settings.models import Setting, SettingsDiff
from flaskbb.core.settings.registry import setting_registry
from flaskbb.extensions import db, pluggy
from flaskbb.utils.database import CRUDMixin


class PluginRegistry(db.Model, CRUDMixin):
    __tablename__ = "plugin_registry"

    id: Mapped[int] = mapped_column(primary_key=True)
    # A plugin's name doubles as its SettingGroup.key - the plugin's
    # flaskbb_load_setting_groups hookimpl must register a group with
    # key == this name for settings/get_settings_form/etc. to find it.
    name: Mapped[str] = mapped_column(db.String(255), unique=True)
    enabled: Mapped[bool] = mapped_column(db.Boolean, default=True)

    def __init__(self, name: str) -> None:
        self.name = name

    @property
    def info(self):
        """Returns some information about the plugin."""
        return pluggy.list_plugin_metadata().get(self.name)

    @property
    def _settings_group(self):
        """The SettingGroup this plugin registered, if any. Plugins
        with no settings (just enable/disable, no configuration) won't
        have registered one."""
        try:
            return setting_registry.group(self.name)
        except KeyError:
            return None

    @property
    def is_installable(self) -> bool:
        """A plugin is installable if it registered a SettingGroup with
        at least one setting to configure."""
        group = self._settings_group
        return group is not None and len(group.settings) > 0

    @property
    def is_installed(self) -> bool:
        """A plugin is installed once every one of its settings has a
        row in the settings table."""
        group = self._settings_group
        if group is None:
            return False
        current_keys = Setting.as_dict().keys()
        return any(s.key in current_keys for s in group.settings)

    @property
    def is_updatable(self) -> bool:
        """A plugin is installed once every one of its settings has a
        row in the settings table."""
        group = self._settings_group
        if group is None:
            return False
        current_keys = Setting.as_dict().keys()
        all_installed = all(s.key in current_keys for s in group.settings)
        any_installed = any(s.key in current_keys for s in group.settings)
        return not all_installed and any_installed

    @property
    def has_settings(self):
        try:
            setting_registry.group(self.name)
            return True
        except KeyError:
            return False

    @property
    def settings(self) -> dict[str, Any]:
        """This plugin's current setting values, keyed by setting key."""
        group = self._settings_group
        if group is None:
            return {}
        current_values = Setting.as_dict()
        return {
            s.key: current_values[s.key]
            for s in group.settings
            if s.key in current_values
        }

    @classmethod
    def get_installed_plugins(cls):
        """Plugins that have registered settings and are enabled."""
        all_plugins = db.session.execute(
            sa.select(PluginRegistry).where(PluginRegistry.enabled == True)
        ).scalars()
        plugins = [p for p in all_plugins if p.is_installed]
        return plugins

    def get_settings_form(self):
        """Generates a settings form based on this plugin's
        SettingGroup - same build_form() used for core settings groups."""
        group = self._settings_group
        if group is None:
            raise ValueError(f"Plugin '{self.name}' has no registered settings")
        return build_form(group)()

    def get_setting_diff(self) -> SettingsDiff | None:
        """Compares this plugin's currently registered settings against
        what's actually stored in the DB - read-only, makes no changes.

        Returns None if the plugin has no registered SettingGroup at
        all (nothing to compare). Use this to show an admin what a
        settings upgrade would actually change before applying it.
        """
        if self._settings_group is None:
            return None
        return Setting.diff_group(self.name)

    def needs_setting_upgrade(self) -> bool:
        """True if this plugin's stored settings differ from what its
        currently loaded code registers - i.e. a new version added or
        removed a setting since the DB was last synced."""
        diff = self.get_setting_diff()
        return diff is not None and diff.has_changes

    def upgrade_settings(self) -> None:
        """Syncs this plugin's settings rows to match its currently
        registered SettingGroup: adds rows for settings that are new,
        removes rows for settings that no longer exist.
        """
        if self._settings_group is None:
            return

        diff = self.get_setting_diff()

        Setting.install_group(self.name)
        Setting.prune_group(self.name)

        if diff is not None:
            pluggy.hook.on_plugin_upgrade(plugin_name=self.name, diff=diff)

    def update_settings(self, form_data: dict[str, Any]) -> None:
        """Updates the given settings of the plugin."""
        Setting.update(form_data)
        pluggy.hook.on_plugin_settings_changed(
            plugin_name=self.name, changed_keys=list(form_data.keys())
        )

    def add_settings(self, force: bool = False) -> None:
        """Adds the settings for this plugin.

        :param force: if True, existing settings for this plugin's settings
            are deleted and re-installed from their defaults first.
            Defaults to False, which only installs settings that don't exist yet
            and leaves any existing values untouched.
        """
        if self._settings_group is None:
            # nothing to install - a plugin with no registered
            # SettingGroup has no defaults to seed
            return

        if force:
            Setting.remove_group(self.name)

        Setting.install_group(self.name)
        pluggy.hook.on_plugin_install(plugin_name=self.name)

    def remove_settings(self) -> None:
        """Deletes all of this plugin's settings from the DB - called
        on plugin uninstall. Delegates straight to Setting.remove_group()
        rather than fetching self._group first, since uninstalling
        should succeed even if the plugin's SettingGroup is no longer
        registered (e.g. the plugin package itself was already removed)."""
        Setting.remove_group(self.name)
