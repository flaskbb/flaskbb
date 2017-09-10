# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.models
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides registration and a basic DB backed key-value
    store for plugins.

    :copyright: (c) 2017 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm.collections import attribute_mapped_collection

from flaskbb.extensions import db
from flaskbb.utils.database import CRUDMixin
from flaskbb.utils.forms import generate_settings_form, SettingsValueTypes

class PluginStore(CRUDMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Unicode(255), nullable=False)
    value = db.Column(db.PickleType, nullable=False)
    # Available types: string, integer, float, boolean, select, selectmultiple
    value_type = db.Column(db.Enum(SettingsValueTypes), nullable=False)
    # Extra attributes like, validation things (min, max length...)
    # For Select*Fields required: choices
    extra = db.Column(db.PickleType, nullable=True)
    plugin_id = db.Column(db.Integer, db.ForeignKey('plugin_registry.id'))

    # Display stuff
    name = db.Column(db.Unicode(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    __table_args__ = (
        UniqueConstraint('key', 'plugin_id', name='plugin_kv_uniq'),
    )

    def __repr__(self):
        return '<PluginSetting plugin={} key={} value={}>'.format(
            self.plugin.name, self.key, self.value
        )


class PluginRegistry(CRUDMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    values = db.relationship(
        'PluginStore',
        collection_class=attribute_mapped_collection('key'),
        cascade='all, delete-orphan',
        backref='plugin'
    )

    def get_settings_form(self):
        return generate_settings_form(self.values.values())()

    def add_settings(self, settings):
        plugin_settings = []
        for key in settings:
            pluginstore = PluginStore()
            pluginstore.key = key
            pluginstore.value = settings[key]['value']
            pluginstore.value_type = settings[key]['value_type']
            pluginstore.extra = settings[key]['extra']
            pluginstore.name = settings[key]['name']
            pluginstore.description = settings[key]['description']
            pluginstore.plugin = self
            plugin_settings.append(pluginstore)

        db.session.add_all(plugin_settings)
        db.session.commit()

    def __repr__(self):
        return '<Plugin name={} enabled={}>'.format(self.name, self.enabled)
