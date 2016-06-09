# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.portal.views
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains the portal view.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import Blueprint, current_app, flash, request
from flask_babelplus import gettext as _
from flask_login import current_user

from flaskbb.utils.helpers import render_template
from flaskbb.forum.models import Topic, Post, Forum
from flaskbb.user.models import User, Group
from flaskbb.utils.helpers import time_diff, get_online_users
from flaskbb.utils.settings import flaskbb_config

portal = Blueprint("portal", __name__, template_folder="templates")


def inject_portal_link():
    return render_template("navigation_snippet.html")


@portal.route("/")
def index():
    page = request.args.get('page', 1, type=int)

    try:
        forum_ids = flaskbb_config["PLUGIN_PORTAL_FORUM_IDS"]
    except KeyError:
        forum_ids = []
        flash(_("Please install the plugin first to configure the forums "
                "which should be displayed."), "warning")

    group_ids = [group.id for group in current_user.groups]
    forums = Forum.query.filter(Forum.groups.any(Group.id.in_(group_ids)))

    # get the news forums - check for permissions
    news_ids = [f.id for f in forums.filter(Forum.id.in_(forum_ids)).all()]
    news = Topic.query.filter(Topic.forum_id.in_(news_ids)).\
        order_by(Topic.id.desc()).\
        paginate(page, flaskbb_config["TOPICS_PER_PAGE"], True)

    # get the recent topics from all to the user available forums (not just the
    # configured ones)
    all_ids = [f.id for f in forums.all()]
    recent_topics = Topic.query.filter(Topic.forum_id.in_(all_ids)).\
        order_by(Topic.last_updated.desc()).\
        limit(flaskbb_config.get("PLUGIN_PORTAL_RECENT_TOPICS", 10))

    user_count = User.query.count()
    topic_count = Topic.query.count()
    post_count = Post.query.count()
    newest_user = User.query.order_by(User.id.desc()).first()

    # Check if we use redis or not
    if not current_app.config["REDIS_ENABLED"]:
        online_users = User.query.filter(User.lastseen >= time_diff()).count()
        online_guests = None
    else:
        online_users = len(get_online_users())
        online_guests = len(get_online_users(guest=True))

    return render_template("index.html", news=news,
                           recent_topics=recent_topics,
                           user_count=user_count, topic_count=topic_count,
                           post_count=post_count, newest_user=newest_user,
                           online_guests=online_guests,
                           online_users=online_users)
