# -*- coding: utf-8 -*-
"""
    flaskbb.forum.views
    ~~~~~~~~~~~~~~~~~~~~

    This module handles the forum logic like creating and viewing
    topics and posts.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import datetime
import math

from flask import (Blueprint, render_template, redirect, url_for, current_app,
                   request, flash)
from flask.ext.login import login_required, current_user

from flaskbb.helpers import last_seen, can_moderate, check_perm
from flaskbb.forum.models import Category, Forum, Topic, Post
from flaskbb.forum.forms import QuickreplyForm, ReplyForm, NewTopicForm
from flaskbb.user.models import User


forum = Blueprint("forum", __name__)


@forum.route("/")
def index():
    categories = Category.query.all()

    # Fetch a few stats about the forum
    user_count = User.query.count()
    topic_count = Topic.query.count()
    post_count = Post.query.count()
    newest_user = User.query.order_by(User.id.desc()).first()

    online_users = User.query.filter(User.lastseen >= last_seen())

    return render_template("forum/index.html", categories=categories,
                           stats={'user_count': user_count,
                                  'topic_count': topic_count,
                                  'post_count': post_count,
                                  'newest_user': newest_user.username,
                                  'online_users': online_users})


@forum.route("/category/<int:category_id>")
def view_category(category_id):
    category = Category.query.filter_by(id=category_id).first()

    return render_template("forum/category.html", category=category)


@forum.route("/forum/<int:forum_id>")
def view_forum(forum_id):
    page = request.args.get('page', 1, type=int)

    forum = Forum.query.filter_by(id=forum_id).first()
    topics = Topic.query.filter_by(forum_id=forum.id).\
        order_by(Topic.last_post_id.desc()).\
        paginate(page, current_app.config['TOPICS_PER_PAGE'], False)

    return render_template("forum/forum.html", forum=forum, topics=topics)


@forum.route("/topic/<int:topic_id>", methods=["POST", "GET"])
def view_topic(topic_id):
    page = request.args.get('page', 1, type=int)

    topic = Topic.query.filter_by(id=topic_id).first()
    posts = Post.query.filter_by(topic_id=topic.id).\
        paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    # Count the topic views
    topic.views += 1
    topic.save()

    form = None

    if not topic.locked:
        if check_perm(current_user, 'postreply', topic.forum):

            form = QuickreplyForm()
            if form.validate_on_submit():
                post = form.save(current_user, topic)
                return view_post(post.id)

    return render_template("forum/topic.html", topic=topic, posts=posts,
                           per_page=current_app.config['POSTS_PER_PAGE'],
                           last_seen=last_seen(), form=form)


@forum.route("/post/<int:post_id>")
def view_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    count = post.topic.post_count
    page = math.ceil(count / current_app.config["POSTS_PER_PAGE"])
    if count > 10:
        page += 1
    else:
        page = 1

    return redirect(url_for("forum.view_topic", topic_id=post.topic.id) +
                    "?page=%d#pid%s" % (page, post.id))


@forum.route("/forum/<int:forum_id>/topic/new", methods=["POST", "GET"])
@login_required
def new_topic(forum_id):
    forum = Forum.query.filter_by(id=forum_id).first()

    if not check_perm(current_user, 'posttopic') or \
        can_moderate(current_user, forum):
        flash("You do not have the permissions to create a new topic.")
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
    topic = Topic.query.filter_by(id=topic_id).first()

    if not check_perm(current_user, 'deletetopic', topic.forum):
        flash("You do not have the permissions to delete the topic")
        return redirect(url_for("forum.view_forum", forum_id=topic.forum_id))

    involved_users = User.query.filter(Post.topic_id == topic.id,
                                       User.id == Post.user_id).all()
    topic.delete(users=involved_users)
    return redirect(url_for("forum.view_forum", forum_id=topic.forum_id))


@forum.route("/topic/<int:topic_id>/post/new", methods=["POST", "GET"])
@login_required
def new_post(topic_id):
    topic = Topic.query.filter_by(id=topic_id).first()

    if topic.locked:
        flash("The topic is locked.")
        return redirect(url_for("forum.view_forum", forum_id=topic.forum_id))

    if not check_perm(current_user, 'postreply', topic.forum):
        flash("You do not have the permissions to delete the topic")
        return redirect(url_for("forum.view_forum", forum_id=topic.forum_id))

    form = ReplyForm()
    if form.validate_on_submit():
        post = form.save(current_user, topic)
        return view_post(post.id)

    return render_template("forum/new_post.html", topic=topic, form=form)


@forum.route("/post/<int:post_id>/edit", methods=["POST", "GET"])
@login_required
def edit_post(post_id):
    post = Post.query.filter_by(id=post_id).first()

    if not check_perm(current_user, 'editpost', post.topic.forum,
        post.user_id):
        flash("You do not have the permissions to edit this post")
        return redirect(url_for('forum.view_topic', topic_id=post.topic_id))

    form = ReplyForm(obj=post)
    if form.validate_on_submit():
        form.populate_obj(post)
        post.date_modified = datetime.datetime.utcnow()
        post.save()
        return redirect(url_for('forum.view_topic', topic_id=post.topic.id))
    else:
        form.content.data = post.content

    return render_template("forum/new_post.html", topic=post.topic, form=form)


@forum.route("/post/<int:post_id>/delete")
@login_required
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id).first()

    if not check_perm(current_user, 'deletepost', post.topic.forum,
        post.user_id):
        flash("You do not have the permissions to edit this post")
        return redirect(url_for('forum.view_topic', topic_id=post.topic_id))

    topic_id = post.topic_id

    post.delete()

    # If the post was the first post in the topic, redirect to the forums
    if post.first_post:
        return redirect(url_for('forum.view_forum',
                                forum_id=post.topic.forum_id))
    return redirect(url_for('forum.view_topic', topic=topic_id))


@forum.route("/who_is_online")
def who_is_online():
    pass

@forum.route("/memberlist")
def memberlist():
    page = request.args.get('page', 1, type=int)

    users = User.query.order_by(User.id).\
        paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    return render_template("forum/memberlist.html",
                           users=users,
                           per_page=current_app.config['USERS_PER_PAGE'])
