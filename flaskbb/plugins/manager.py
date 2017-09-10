# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.manager
    ~~~~~~~~~~~~~~~~~~~~~~~

    Plugin Manager for FlaskBB

    :copyright: 2017, the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""
from pkg_resources import (DistributionNotFound, VersionConflict,
                           iter_entry_points)

import pluggy
from flaskbb.utils.helpers import parse_pkg_metadata


class FlaskBBPluginManager(pluggy.PluginManager):
    """Overwrites :class:`pluggy.PluginManager` to add FlaskBB
    specific stuff.
    """

    def __init__(self, project_name, implprefix=None):
        super(FlaskBBPluginManager, self).__init__(
            project_name=project_name, implprefix=implprefix
        )
        self._plugin_metadata = {}
        self._disabled_plugins = []

    def load_setuptools_entrypoints(self, entrypoint_name):
        """Load modules from querying the specified setuptools entrypoint name.
        Return the number of loaded plugins. """
        for ep in iter_entry_points(entrypoint_name):
            if self.get_plugin(ep.name):
                continue

            if self.is_blocked(ep.name):
                self._disabled_plugins.append((ep.name, ep.dist))
                continue

            try:
                plugin = ep.load()
            except DistributionNotFound:
                continue
            except VersionConflict as e:
                raise pluggy.PluginValidationError(
                    "Plugin %r could not be loaded: %s!" % (ep.name, e)
                )
            self.register(plugin, name=ep.name)
            self._plugin_distinfo.append((plugin, ep.dist))
            self._plugin_metadata[ep.name] = parse_pkg_metadata(ep.dist.key)
        return len(self._plugin_distinfo)

    def get_metadata(self, name):
        """Returns the metadata for a given name."""
        return self._plugin_metadata.get(name)

    def list_plugin_metadata(self):
        """Returns the metadata for all plugins"""
        return self._plugin_metadata

    def list_disabled_plugins(self):
        """Returns a name/distinfo tuple pairs of disabled plugins."""
        return self._disabled_plugins
