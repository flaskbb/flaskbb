# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.models
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides registration and a basic DB backed key-value
    store for plugins.

    :copyright: (c) 2017 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import current_app
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm.collections import attribute_mapped_collection

from flaskbb._compat import itervalues
from flaskbb.extensions import db
from flaskbb.utils.database import CRUDMixin
from flaskbb.utils.forms import SettingValueType, generate_settings_form


class PluginStore(CRUDMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Unicode(255), nullable=False)
    value = db.Column(db.PickleType, nullable=False)
    # Available types: string, integer, float, boolean, select, selectmultiple
    value_type = db.Column(db.Enum(SettingValueType), nullable=False)
    # Extra attributes like, validation things (min, max length...)
    # For Select*Fields required: choices
    extra = db.Column(db.PickleType, nullable=True)
    plugin_id = db.Column(
        db.Integer, db.ForeignKey("plugin_registry.id", ondelete="CASCADE")
    )

    # Display stuff
    name = db.Column(db.Unicode(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    __table_args__ = (UniqueConstraint("key", "plugin_id", name="plugin_kv_uniq"),)

    def __repr__(self):
        return "<PluginSetting plugin={} key={} value={}>".format(
            self.plugin.name, self.key, self.value
        )

    @classmethod
    def get_or_create(cls, plugin_id, key):
        """Returns the PluginStore object or an empty one.
        The created object still needs to be added to the database session
        """
        obj = cls.query.filter_by(plugin_id=plugin_id, key=key).first()

        if obj is not None:
            return obj
        return PluginStore()

    @classmethod
    def from_dict(cls, plugin, key, dct):
        store = cls()
        store.populate(plugin, key, dct)
        return store

    def populate(self, plugin, key, dct):
        self.key = key
        self.plugin = plugin
        self.value = dct["value"]
        self.value_type = dct["value_type"]
        self.extra = dct["extra"]
        self.name = dct["name"]
        self.description = dct["description"]


class PluginRegistry(CRUDMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    values = db.relationship(
        "PluginStore",
        collection_class=attribute_mapped_collection("key"),
        backref="plugin",
        cascade="all, delete-orphan",
    )

    @property
    def settings(self):
        """Returns a dict with contains all the settings in a plugin."""
        return {kv.key: kv.value for kv in itervalues(self.values)}

    @property
    def info(self):
        """Returns some information about the plugin."""
        return current_app.pluggy.list_plugin_metadata().get(self.name, {})

    @property
    def is_installable(self):
        """Returns True if the plugin has settings that can be installed."""
        plugin_module = current_app.pluggy.get_plugin(self.name)
        return getattr(plugin_module, "SETTINGS", False)

    @property
    def is_installed(self):
        """Returns True if the plugin is installed."""
        if self.settings:
            return True
        return False

    def get_settings_form(self):
        """Generates a settings form based on the settings."""
        return generate_settings_form(self.values.values())()

    def update_settings(self, settings):
        """Updates the given settings of the plugin.

        :param settings: A dictionary containing setting items.
        """
        pluginstore = PluginStore.query.filter(
            PluginStore.plugin_id == self.id, PluginStore.key.in_(settings.keys())
        ).all()

        setting_list = []
        for pluginsetting in pluginstore:
            pluginsetting.value = settings[pluginsetting.key]
            setting_list.append(pluginsetting)
        db.session.add_all(setting_list)
        db.session.commit()

    def add_settings(self, settings, force=False):
        """Adds the given settings to the plugin.

        :param settings: A dictionary containing setting items.
        :param force: Forcefully overwrite existing settings.
        """
        plugin_settings = []
        for key in settings:
            if force:
                with db.session.no_autoflush:
                    pluginstore = PluginStore.get_or_create(self.id, key)
            else:
                # otherwise we assume that no such setting exist
                pluginstore = PluginStore()

            pluginstore.key = key
            pluginstore.plugin = self
            pluginstore.value = settings[key]["value"]
            pluginstore.value_type = settings[key]["value_type"]
            pluginstore.extra = settings[key]["extra"]
            pluginstore.name = settings[key]["name"]
            pluginstore.description = settings[key]["description"]
            plugin_settings.append(pluginstore)

        db.session.add_all(plugin_settings)
        db.session.commit()

    def upgrade_settings(self):
        plugin_module = current_app.pluggy.get_plugin(self.name)
        settings = plugin_module.SETTINGS

        deleted_settings = [
            (key, s) for key, s in self.values.items() if key not in settings
        ]
        added_settings = [
            PluginStore.from_dict(self, key, values)
            for key, values in settings.items()
            if key not in self.values
        ]
        # but what do here?
        # updated_settings = []

        db.session.add_all(added_settings)
        for setting in deleted_settings:
            db.session.delete(setting[1])

        db.session.commit()

        return {
            "added": [p.key for p in added_settings],
            "removed": [d[0] for d in deleted_settings],
            "updated": []
        }

    def has_new_settings(self):
        if not self.is_installable or not self.is_installed:
            return False

        plugin_module = current_app.pluggy.get_plugin(self.name)
        settings = plugin_module.SETTINGS

        return set(settings.keys()) != set(self.values.keys())

    def __repr__(self):
        return "<Plugin name={} enabled={}>".format(self.name, self.enabled)
