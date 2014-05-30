# -*- coding: utf-8 -*-
from flask import Blueprint, current_app, flash
from flaskbb.utils.helpers import render_template
from flaskbb.forum.models import Topic, Post
from flaskbb.user.models import User
from flaskbb.utils.helpers import time_diff, get_online_users


portal = Blueprint("portal", __name__, template_folder="templates")


def inject_portal_link():
    return render_template("navigation_snippet.html")


@portal.route("/")
def index():
    try:
        forum_ids = current_app.config["PLUGIN_PORTAL_FORUM_IDS"]
    except KeyError:
        forum_ids = [1]
        flash("Please install the plugin first to configure the forums "
              "which should be displayed", "warning")

    news = Topic.query.filter(Topic.forum_id.in_(forum_ids)).all()
    recent_topics = Topic.query.order_by(Topic.date_created).limit(5).offset(0)

    user_count = User.query.count()
    topic_count = Topic.query.count()
    post_count = Post.query.count()
    newest_user = User.query.order_by(User.id.desc()).first()

    # Check if we use redis or not
    if not current_app.config["REDIS_ENABLED"]:
        online_users = User.query.filter(User.lastseen >= time_diff()).count()

        # Because we do not have server side sessions, we cannot check if there
        # are online guests
        online_guests = None
    else:
        online_users = len(get_online_users())
        online_guests = len(get_online_users(guest=True))

    return render_template("index.html", news=news, recent_topics=recent_topics,
                           user_count=user_count, topic_count=topic_count,
                           post_count=post_count, newest_user=newest_user,
                           online_guests=online_guests,
                           online_users=online_users)
