from flask import Blueprint
from flaskbb.utils.helpers import render_template
from flaskbb.forum.models import Topic


FORUM_IDS = [1]

portal = Blueprint("portal", __name__, template_folder="templates")


def inject_portal_link():
    return render_template("navigation_snippet.html")


@portal.route("/")
def index():
    topics = Topic.query.filter(Topic.forum_id.in_(FORUM_IDS)).all()
    return render_template("index.html", topics=topics)
