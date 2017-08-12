# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.models
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides registration and a basic DB backed key-value store for plugins.

    :copyright: (c) 2017 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm.collections import attribute_mapped_collection

from flaskbb.extensions import db


class PluginStore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False)
    value = db.Column(db.Unicode(255))
    plugin_id = db.Column(db.Integer, db.ForeignKey('plugin_registry.id'))

    __table_args__ = (UniqueConstraint('name', 'plugin_id', name='plugin_kv_uniq'), )

    def __repr__(self):
        return '<FlaskBBPluginSetting plugin={} name={} value={}>'.format(
            self.plugin.name, self.name, self.value
        )


class PluginRegistry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    values = db.relationship(
        'PluginStore',
        collection_class=attribute_mapped_collection('name'),
        cascade='all, delete-orphan',
        backref='plugin'
    )
    settings = association_proxy(
        'values', 'value', creator=lambda k, v: PluginStore(name=k, value=v)
    )

    def __repr__(self):
        return '<FlaskBBPlugin name={} enabled={}>'.format(self.name, self.id)
