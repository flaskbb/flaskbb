# -*- coding: utf-8 -*-
"""
flaskbb.plugins.manager
~~~~~~~~~~~~~~~~~~~~~~~

Plugin Manager for FlaskBB

:copyright: 2017, the FlaskBB Team
:license: BSD, see LICENSE for more details
"""

import logging
import string
from importlib.metadata import PackageMetadata
from typing import TYPE_CHECKING, TypeAlias, override

if TYPE_CHECKING:
    from importlib.metadata import Distribution

import pluggy
from pluggy._manager import DistFacade

logger = logging.getLogger(__name__)

_Plugin: TypeAlias = object


class DistMeta:
    name: str
    package_name: str
    url: str | None = None
    author: str | None = None
    license: str | None = None
    summary: str | None
    version: str

    def __init__(self, dist: Distribution, name: str) -> None:
        self.package_name = dist.name
        self.url = self._get_project_url(dist.metadata)
        self.author = self._get_author(dist.metadata)
        self.license = self._get_license(dist.metadata)
        self.summary = dist.metadata.get("Summary")
        self.version = dist.version
        self.name = name

    def _get_license(self, metadata: PackageMetadata):
        license: str | None = metadata.get("License-Expression")
        if license is not None:
            return license

        if license is None and metadata.get("License-File") is not None:
            return f"See the provided {metadata.get('License-File')}"

        return ""

    def _get_author(self, metadata: PackageMetadata):
        if metadata.get("Maintainer") is not None:
            return metadata.get("Maintainer")
        if metadata.get("Maintainer-Email") is not None:
            return self._parse_name_with_email(metadata.get_all("Maintainer-Email"))
        if metadata.get("Author") is not None:
            return metadata.get("Author")
        if metadata.get("Author-Email") is not None:
            return self._parse_name_with_email(metadata.get_all("Author-Email"))
        return ""

    def _parse_name_with_email(self, mails: list[str] | None):
        if mails is None:
            return ""
        names = [mail.split("<")[0].strip() for mail in mails]
        return ", ".join(names)

    def _get_project_url(self, metadata: PackageMetadata):
        # https://packaging.python.org/en/latest/specifications/well-known-project-urls/#well-known-labels
        names = ["homepage", "source", "sourcecode", "repository"]
        urls: list[str] | None = metadata.get_all("Project-Url")
        if not urls:
            return ""
        for url in sorted(urls):
            name, uri = url.split(",")
            if self._normalize_label(name) in names:
                return uri
        # uri not found
        return ""

    def _normalize_label(self, label: str) -> str:
        chars_to_remove = string.punctuation + string.whitespace
        removal_map = str.maketrans("", "", chars_to_remove)
        return label.translate(removal_map).lower()


class FlaskBBPluginManager(pluggy.PluginManager):
    """Overwrites :class:`pluggy.PluginManager` to add FlaskBB
    specific stuff.
    """

    def __init__(self, project_name: str):
        super(FlaskBBPluginManager, self).__init__(project_name=project_name)
        self._plugin_metadata: dict[str, DistMeta] = {}
        self._disabled_plugins: dict[str, _Plugin] = {}

        # we maintain a seperate dict for flaskbb.* internal plugins
        self._internal_name2plugin: dict[str, _Plugin] = {}

    @override
    def register(
        self, plugin: _Plugin, name: str | None = None, internal: bool = False
    ):
        """Register a plugin and return its canonical name or None
        if the name is blocked from registering.
        Raise a ValueError if the plugin is already registered.
        """
        # internal plugins are stored in self._plugin2hookcallers
        name = super(FlaskBBPluginManager, self).register(plugin, name)
        if not internal:
            return name

        if name is None:
            logger.error("Couldn't register plugin {}".format(plugin))
            return None

        self._internal_name2plugin[name] = self._name2plugin[name]
        return name

    @override
    def unregister(self, plugin: _Plugin | None = None, name: str | None = None):
        """Unregister a plugin object and all its contained hook implementations
        from internal data structures.
        """
        plugin = super(FlaskBBPluginManager, self).unregister(plugin=plugin, name=name)

        name = self.get_name(plugin)
        if name is None:
            return

        if self._internal_name2plugin.get(name):
            del self._internal_name2plugin[name]

        return plugin

    @override
    def set_blocked(self, name: str):
        """Block registrations of the given name, unregister if already
        registered.
        """
        super(FlaskBBPluginManager, self).set_blocked(name)
        self._internal_name2plugin[name] = None

    @override
    def is_blocked(self, name: str):
        """Return True if the name blockss registering plugins of that name."""
        blocked = super(FlaskBBPluginManager, self).is_blocked(name)

        return (
            blocked
            or name in self._internal_name2plugin
            and self._internal_name2plugin[name] is None
        )

    @override
    def get_plugin(self, name: str):
        """Return a plugin or None for the given name."""
        plugin = super(FlaskBBPluginManager, self).get_plugin(name)
        return self._internal_name2plugin.get(name, plugin)

    @override
    def get_name(self, plugin: _Plugin):
        """Return name for registered plugin or None if not registered."""
        name = super(FlaskBBPluginManager, self).get_name(plugin)
        if name:
            return name

        for name, val in self._internal_name2plugin.items():
            if plugin == val:
                return name

    @override
    def load_setuptools_entrypoints(self, group: str, name: str | None = None) -> int:
        """Load modules from querying the specified setuptools entrypoint name.
        Return the number of loaded plugins."""
        logger.info("Loading plugins under entrypoint {}".format(group))
        import importlib.metadata

        count = 0
        for dist in list(importlib.metadata.distributions()):
            for ep in dist.entry_points:
                if (
                    ep.group != group
                    or (name is not None and ep.name != name)
                    # already registered
                    or self.get_plugin(ep.name)
                ):
                    continue

                plugin = ep.load()
                self._plugin_distinfo.append((plugin, DistFacade(dist)))
                self._plugin_metadata[ep.name] = DistMeta(dist, ep.name)

                if self.is_blocked(ep.name):
                    continue

                self.register(plugin, name=ep.name)

                count += 1
                logger.info("Loaded plugin: {}".format(ep.name))

        logger.info(f"Loaded {count} plugins for entrypoint {group}")
        return count

    def get_metadata(self, name: str):
        """Returns the metadata for a given name."""
        return self._plugin_metadata.get(name)

    def list_name(self):
        """Returns only the enabled plugin names."""
        return list(self._name2plugin.keys())

    def list_internal_name_plugin(self):
        """Returns a list of internal name/plugin pairs."""
        return self._internal_name2plugin.items()

    def list_plugin_metadata(self):
        """Returns the metadata for all plugins"""
        return self._plugin_metadata

    def list_disabled_plugins(self):
        """Returns a name/distinfo tuple pairs of disabled plugins."""
        return self._disabled_plugins.values()

    def get_disabled_plugins(self):
        """Returns a list with disabled plugins."""
        return self._disabled_plugins.keys()

    def get_internal_plugins(self):
        """Returns a set of registered internal plugins."""
        return set(self._internal_name2plugin.values())

    def get_external_plugins(self):
        """Returns a set of registered external plugins."""
        return set(self.get_plugins() - self.get_internal_plugins())
