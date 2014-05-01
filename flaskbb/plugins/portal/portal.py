# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.portal
    ~~~~~~~~~~~~~~~~~~~~~~

    This plugin implements a portal. You can choose which topics and posts
    from forums are displayed.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flaskbb.extensions import db


class PortalModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey("forums.id"))
