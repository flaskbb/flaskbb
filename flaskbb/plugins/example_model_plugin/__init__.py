# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.plugin_name
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    A Portal Plugin for FlaskBB.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask_plugins import connect_event

from flaskbb.plugins import FlaskBBPlugin,db_for_plugin
from flaskbb.utils.populate import (create_settings_from_fixture,
                                    delete_settings_from_fixture)
from flaskbb.extensions import db
from flaskbb.forum.models import Forum

from .views import plugin_bp, inject_navigation_link

__version__ = "0.1"
__plugin__ = "HelloWorldPlugin"


fixture = (
    ('plugin_plugin_name', {
        'name': "Plugin Name Settings",
        "description": "Configure the Plugin Name Plugin",
        "settings": (
            ('plugin_name_display_in_navigation', {
                'value':       True,
                'value_type':  "boolean",
                'name':        "Show Link in Navigation",
                'description': "If enabled, it will show the link in the navigation"
            }),
        ),
    }),
)

db=db_for_plugin(__name__,db)

class MyModel(db.Model):
    __tablename__='my_model'
    field1=db.Column(db.String,primary_key=True)

moderators = db.Table(
    'test_table',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id'),
              nullable=False),
    db.Column('forum_id', db.Integer(),
              db.ForeignKey('forums.id', use_alter=True, name="fk_forum_id"),
              nullable=False))

class HelloWorldPlugin(FlaskBBPlugin):
    settings_key = 'plugin_plugin_name'

    def setup(self):
        self.register_blueprint(plugin_bp, url_prefix="/plugin-name")
        connect_event("before-first-navigation-element", inject_navigation_link)

    def install(self):
        create_settings_from_fixture(fixture)

    def uninstall(self):
        delete_settings_from_fixture(fixture)
