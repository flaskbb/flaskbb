# -*- coding: utf-8 -*-
"""
    flaskbb.forum.views
    ~~~~~~~~~~~~~~~~~~~~

    This module handles the forum logic like creating and viewing
    topics and posts.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import datetime
import math

from flask import (Blueprint, render_template, redirect, url_for, current_app,
                   request, flash)
from flask.ext.login import login_required, current_user

from flaskbb.extensions import db
from flaskbb.utils.helpers import (can_post_reply, can_delete_topic,
                                   can_edit_post, can_post_topic,
                                   can_delete_post, can_lock_topic,
                                   get_online_users, time_diff)
from flaskbb.forum.models import Forum, Topic, Post, ForumsRead, TopicsRead
from flaskbb.forum.forms import QuickreplyForm, ReplyForm, NewTopicForm
from flaskbb.forum.helpers import get_forums
from flaskbb.user.models import User


forum = Blueprint("forum", __name__)


@forum.route("/")
def index():
    # Get the categories and forums
    if current_user.is_authenticated():
        categories_query = Forum.query.\
            outerjoin(ForumsRead,
                      db.and_(ForumsRead.forum_id == Forum.id,
                              ForumsRead.user_id == current_user.id)).\
            add_entity(ForumsRead).\
            order_by(Forum.position.asc()).\
            all()
        categories = get_forums(categories_query, current_user=True)
    else:
        categories_query = Forum.query.order_by(Forum.position.asc()).all()
        categories = get_forums(categories_query, current_user=False)

    # Fetch a few stats about the forum
    user_count = User.query.count()
    topic_count = Topic.query.count()
    post_count = Post.query.count()
    newest_user = User.query.order_by(User.id.desc()).first()

    # Check if we use redis or not
    if not current_app.config["USE_REDIS"]:
        online_users = User.query.filter(User.lastseen >= time_diff()).count()
        online_guests = None
    else:
        online_users = len(get_online_users())
        online_guests = len(get_online_users(guest=True))

    return render_template("forum/index.html",
                           categories=categories,
                           user_count=user_count,
                           topic_count=topic_count,
                           post_count=post_count,
                           newest_user=newest_user,
                           online_users=online_users,
                           online_guests=online_guests)


@forum.route("/<int:forum_id>")
def view_forum(forum_id):
    page = request.args.get('page', 1, type=int)

    if current_user.is_authenticated():
        forum = Forum.query.filter(Forum.id == forum_id).first_or_404()

        subforums = Forum.query.\
            filter(Forum.parent_id == forum.id).\
            outerjoin(ForumsRead,
                      db.and_(ForumsRead.forum_id == Forum.id,
                              ForumsRead.user_id == current_user.id)).\
            add_entity(ForumsRead).\
            all()

        topics = Topic.query.filter_by(forum_id=forum.id).\
            filter(Post.topic_id == Topic.id).\
            outerjoin(TopicsRead,
                      db.and_(TopicsRead.topic_id == Topic.id,
                              TopicsRead.user_id == current_user.id)).\
            add_entity(TopicsRead).\
            order_by(Post.id.desc()).\
            paginate(page, current_app.config['TOPICS_PER_PAGE'], True)
    else:
        forum = Forum.query.filter(Forum.id == forum_id).first_or_404()

        subforums = Forum.query.filter(Forum.parent_id == forum.id).all()
        # This isn't really nice imho, but "add_entity" (see above)
        # makes a list with tuples
        subforums = [(item, None) for item in subforums]

        topics = Topic.query.filter_by(forum_id=forum.id).\
            filter(Post.topic_id == Topic.id).\
            order_by(Post.id.desc()).\
            paginate(page, current_app.config['TOPICS_PER_PAGE'], True, True)

    return render_template("forum/forum.html",
                           forum=forum, topics=topics, subforums=subforums)


@forum.route("/markread")
@forum.route("/<int:forum_id>/markread")
def markread(forum_id=None):

    if not current_user.is_authenticated():
        flash("We do not support cookie based unread forums yet.", "danger")
        return redirect(url_for("forum.index"))

    # Mark a single forum as read
    if forum_id:
        forum = Forum.query.filter_by(id=forum_id).first_or_404()
        for topic in forum.topics:
            topic.update_read(current_user, forum)
        return redirect(url_for("forum.view_forum", forum_id=forum.id))

    # Mark all forums as read
    # TODO: Improve performance
    forums = Forum.query.all()
    for forum in forums:
        if forum.is_category:
            continue

        for topic in forum.topics:
            topic.update_read(current_user, forum)

    return redirect(url_for("forum.index"))


@forum.route("/topic/<int:topic_id>", methods=["POST", "GET"])
def view_topic(topic_id):
    page = request.args.get('page', 1, type=int)

    topic = Topic.query.filter_by(id=topic_id).first()
    posts = Post.query.filter_by(topic_id=topic.id).\
        paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    # Count the topic views
    topic.views += 1

    # Update the topicsread status if the user hasn't read it
    topic.update_read(current_user, topic.forum)
    topic.save()

    form = None

    if not topic.locked \
        and not topic.forum.locked \
        and can_post_reply(user=current_user,
                           forum=topic.forum):

            form = QuickreplyForm()
            if form.validate_on_submit():
                post = form.save(current_user, topic)
                return view_post(post.id)

    return render_template("forum/topic.html", topic=topic, posts=posts,
                           last_seen=time_diff(), form=form)


@forum.route("/post/<int:post_id>")
def view_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    count = post.topic.post_count
    page = math.ceil(count / current_app.config["POSTS_PER_PAGE"])
    if count > 10:
        page += 1
    else:
        page = 1

    return redirect(url_for("forum.view_topic", topic_id=post.topic.id) +
                    "?page=%d#pid%s" % (page, post.id))


@forum.route("/<int:forum_id>/topic/new", methods=["POST", "GET"])
@login_required
def new_topic(forum_id):
    forum = Forum.query.filter_by(id=forum_id).first_or_404()

    if forum.locked:
        flash("This forum is locked; you cannot submit new topics or posts.",
              "danger")
        return redirect(url_for('forum.view_forum', forum_id=forum.id))

    if not can_post_topic(user=current_user, forum=forum):
        flash("You do not have the permissions to create a new topic.",
              "danger")
        return redirect(url_for('forum.view_forum', forum_id=forum.id))

    form = NewTopicForm()
    if form.validate_on_submit():
        topic = form.save(current_user, forum)

        # redirect to the new topic
        return redirect(url_for('forum.view_topic', topic_id=topic.id))
    return render_template("forum/new_topic.html", forum=forum, form=form)


@forum.route("/topic/<int:topic_id>/delete")
@login_required
def delete_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if not can_delete_topic(user=current_user, forum=topic.forum,
                            post_user_id=topic.first_post.user_id):

        flash("You do not have the permissions to delete the topic", "danger")
        return redirect(url_for("forum.view_forum", forum_id=topic.forum_id))

    involved_users = User.query.filter(Post.topic_id == topic.id,
                                       User.id == Post.user_id).all()
    topic.delete(users=involved_users)
    return redirect(url_for("forum.view_forum", forum_id=topic.forum_id))


@forum.route("/topic/<int:topic_id>/lock")
@login_required
def lock_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if not can_lock_topic(user=current_user, forum=topic.forum):
        flash("Yo do not have the permissions to lock this topic", "danger")
        return redirect(url_for("forum.view_topic", topic_id=topic.id))

    topic.locked = True
    topic.save()
    return redirect(url_for("forum.view_topic", topic_id=topic.id))


@forum.route("/topic/<int:topic_id>/unlock")
@login_required
def unlock_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    # Unlock is basically the same as lock
    if not can_lock_topic(user=current_user, forum=topic.forum):
        flash("Yo do not have the permissions to unlock this topic", "danger")
        return redirect(url_for("forum.view_topic", topic_id=topic.id))

    topic.locked = False
    topic.save()
    return redirect(url_for("forum.view_topic", topic_id=topic.id))


@forum.route("/topic/<int:topic_id>/move")
@login_required
def move_topic(topic_id):
    pass


@forum.route("/topic/<int:topic_id>/post/new", methods=["POST", "GET"])
@login_required
def new_post(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if topic.forum.locked:
        flash("This forum is locked; you cannot submit new topics or posts.",
              "danger")
        return redirect(url_for('forum.view_forum', forum_id=topic.forum.id))

    if topic.locked:
        flash("The topic is locked.", "danger")
        return redirect(url_for("forum.view_forum", forum_id=topic.forum_id))

    if not can_post_reply(user=current_user, forum=topic.forum):
        flash("You do not have the permissions to delete the topic", "danger")
        return redirect(url_for("forum.view_forum", forum_id=topic.forum_id))

    form = ReplyForm()
    if form.validate_on_submit():
        post = form.save(current_user, topic)
        return view_post(post.id)

    return render_template("forum/new_post.html", topic=topic, form=form)


@forum.route("/post/<int:post_id>/edit", methods=["POST", "GET"])
@login_required
def edit_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()

    if post.topic.forum.locked:
        flash("This forum is locked; you cannot submit new topics or posts.",
              "danger")
        return redirect(url_for("forum.view_forum",
                                forum_id=post.topic.forum.id))

    if post.topic.locked:
        flash("The topic is locked.", "danger")
        return redirect(url_for("forum.view_forum",
                                forum_id=post.topic.forum_id))

    if not can_edit_post(user=current_user, forum=post.topic.forum,
                         post_user_id=post.user_id):
        flash("You do not have the permissions to edit this post", "danger")
        return redirect(url_for('forum.view_topic', topic_id=post.topic_id))

    form = ReplyForm()
    if form.validate_on_submit():
        form.populate_obj(post)
        post.date_modified = datetime.datetime.utcnow()
        post.save()
        return redirect(url_for("forum.view_topic", topic_id=post.topic.id))
    else:
        form.content.data = post.content

    return render_template("forum/new_post.html", topic=post.topic, form=form)


@forum.route("/post/<int:post_id>/delete")
@login_required
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()

    if not can_delete_post(user=current_user, forum=post.topic.forum,
                           post_user_id=post.user_id):
        flash("You do not have the permissions to edit this post", "danger")
        return redirect(url_for('forum.view_topic', topic_id=post.topic_id))

    topic_id = post.topic_id

    post.delete()

    # If the post was the first post in the topic, redirect to the forums
    if post.first_post:
        return redirect(url_for('forum.view_forum',
                                forum_id=post.topic.forum_id))
    return redirect(url_for('forum.view_topic', topic_id=topic_id))


@forum.route("/who_is_online")
def who_is_online():
    if current_app.config['USE_REDIS']:
        online_users = get_online_users()
    else:
        online_users = User.query.filter(User.lastseen >= time_diff()).all()
    return render_template("forum/online_users.html",
                           online_users=online_users)


@forum.route("/memberlist")
def memberlist():
    page = request.args.get('page', 1, type=int)

    users = User.query.order_by(User.id).\
        paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    return render_template("forum/memberlist.html",
                           users=users)


@forum.route("/topictracker")
def topictracker():
    page = request.args.get("page", 1, type=int)
    topics = current_user.tracked_topics.\
        outerjoin(TopicsRead,
                  db.and_(TopicsRead.topic_id == Topic.id,
                          TopicsRead.user_id == current_user.id)).\
        add_entity(TopicsRead).\
        order_by(Post.id.desc()).\
        paginate(page, current_app.config['TOPICS_PER_PAGE'], True)

    return render_template("forum/topictracker.html", topics=topics)


@forum.route("/topictracker/<topic_id>/add")
def track_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()
    current_user.track_topic(topic)
    current_user.save()
    return redirect(url_for("forum.view_topic", topic_id=topic.id))


@forum.route("/topictracker/<topic_id>/delete")
def untrack_topic(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()
    current_user.untrack_topic(topic)
    current_user.save()
    return redirect(url_for("forum.view_topic", topic_id=topic.id))
