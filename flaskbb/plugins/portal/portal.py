# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.portal
    ~~~~~~~~~~~~~~~~~~~~~~

    This plugin implements a portal. You can choose which topics and posts
    from forums are displayed.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import Blueprint
from flaskbb.extensions import db
from flaskbb.utils.helpers import render_template


portal = Blueprint("portal", __name__, template_folder="templates")


class PortalModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey("forums.id"))


@portal.route("/portal")
def portal_index():
    return render_template("portal.html")
