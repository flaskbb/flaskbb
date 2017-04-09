# -*- coding: utf-8 -*-
"""
    flaskbb.plugins
    ~~~~~~~~~~~~~~~

    This module contains the Plugin class used by all Plugins for FlaskBB.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import warnings
from flask import current_app
from flask_plugins import Plugin

from flaskbb.management.models import SettingsGroup


class FlaskBBPluginDeprecationWarning(DeprecationWarning):
    pass


warnings.simplefilter("always", FlaskBBPluginDeprecationWarning)


class FlaskBBPlugin(Plugin):
    #: This is the :class:`SettingsGroup` key - if your the plugin needs to
    #: install additional things you must set it, else it won't install
    #: anything.
    settings_key = None

    @property
    def has_settings(self):
        """Is ``True`` if the Plugin **can** be installed."""
        if self.settings_key is not None:
            return True
        return False

    @property
    def installed(self):
        is_installed = False
        if self.has_settings:
            group = SettingsGroup.query.\
                filter_by(key=self.settings_key).\
                first()
            is_installed = group and len(group.settings.all()) > 0
        return is_installed

    @property
    def uninstallable(self):
        """Is ``True`` if the Plugin **can** be uninstalled."""
        warnings.warn(
            "self.uninstallable is deprecated. Use self.installed instead.",
            FlaskBBPluginDeprecationWarning
        )
        return self.installed

    @property
    def installable(self):
        warnings.warn(
            "self.installable is deprecated. Use self.has_settings instead.",
            FlaskBBPluginDeprecationWarning
        )
        return self.has_settings

    # Some helpers
    def register_blueprint(self, blueprint, **kwargs):
        """Registers a blueprint.

        :param blueprint: The blueprint which should be registered.
        """
        current_app.register_blueprint(blueprint, **kwargs)
