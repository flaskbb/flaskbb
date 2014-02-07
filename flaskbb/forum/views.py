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

from flask import (Blueprint, redirect, url_for, current_app,
                   request, flash)
from flask.ext.login import login_required, current_user

from flaskbb.extensions import db
from flaskbb.utils.helpers import get_online_users, time_diff, render_template
from flaskbb.utils.permissions import (can_post_reply, can_post_topic,
                                       can_delete_topic, can_delete_post,
                                       can_edit_post, can_lock_topic,
                                       can_move_topic)
from flaskbb.forum.models import (Category, Forum, Topic, Post, ForumsRead,
                                  TopicsRead)
from flaskbb.forum.forms import QuickreplyForm, ReplyForm, NewTopicForm
from flaskbb.utils.helpers import get_forums
from flaskbb.user.models import User


forum = Blueprint("forum", __name__)


@forum.route("/")
def index():
    # Get the categories and forums
    if current_user.is_authenticated():
        forum_query = Category.query.\
            join(Forum, Category.id == Forum.category_id).\
            outerjoin(ForumsRead,
                      db.and_(ForumsRead.forum_id == Forum.id,
                              ForumsRead.user_id == current_user.id)).\
            add_entity(Forum).\
            add_entity(ForumsRead).\
            order_by(Category.id, Category.position, Forum.position).\
            all()
    else:
        # we do not need to join the ForumsRead because the user isn't
        # signed in
        forum_query = Category.query.\
            join(Forum, Category.id == Forum.category_id).\
            add_entity(Forum).\
            order_by(Category.id, Category.position, Forum.position).\
            all()

        forum_query = [(category, forum, None)
                       for category, forum in forum_query]

    categories = get_forums(forum_query)

    # Fetch a few stats about the forum
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

    return render_template("forum/index.html",
                           categories=categories,
                           user_count=user_count,
                           topic_count=topic_count,
                           post_count=post_count,
                           newest_user=newest_user,
                           online_users=online_users,
                           online_guests=online_guests)


@forum.route("/category/<int:category_id>")
def view_category(category_id):
    if current_user.is_authenticated():
        forum_query = Category.query.\
            filter(Category.id == category_id).\
            join(Forum, Category.id == Forum.category_id).\
            outerjoin(ForumsRead,
                      db.and_(ForumsRead.forum_id == Forum.id,
                              ForumsRead.user_id == 1)).\
            add_entity(Forum).\
            add_entity(ForumsRead).\
            order_by(Forum.position).\
            all()
    else:
        # we do not need to join the ForumsRead because the user isn't
        # signed in
        forum_query = Category.query.\
            filter(Category.id == category_id).\
            join(Forum, Category.id == Forum.category_id).\
            add_entity(Forum).\
            order_by(Forum.position).\
            all()

        forum_query = [(category, forum, None)
                       for category, forum in forum_query]

    category = get_forums(forum_query)
    return render_template("forum/category.html", categories=category)


@forum.route("/forum/<int:forum_id>")
def view_forum(forum_id):
    page = request.args.get('page', 1, type=int)

    if current_user.is_authenticated():
        forum = Forum.query.\
            filter(Forum.id == forum_id).\
            options(db.joinedload("category")).\
            outerjoin(ForumsRead,
                      db.and_(ForumsRead.forum_id == Forum.id,
                              ForumsRead.user_id == current_user.id)).\
            add_entity(ForumsRead).\
            first_or_404()

        topics = Topic.query.filter_by(forum_id=forum[0].id).\
            filter(Post.topic_id == Topic.id).\
            outerjoin(TopicsRead,
                      db.and_(TopicsRead.topic_id == Topic.id,
                              TopicsRead.user_id == current_user.id)).\
            add_entity(TopicsRead).\
            order_by(Post.id.desc()).\
            paginate(page, current_app.config['TOPICS_PER_PAGE'], True)
    else:
        forum = Forum.query.filter(Forum.id == forum_id).first_or_404()
        forum = (forum, None)

        topics = Topic.query.filter_by(forum_id=forum[0].id).\
            filter(Post.topic_id == Topic.id).\
            order_by(Post.id.desc()).\
            paginate(page, current_app.config['TOPICS_PER_PAGE'], True, True)

    return render_template("forum/forum.html", forum=forum, topics=topics)


@forum.route("/topic/<int:topic_id>", methods=["POST", "GET"])
def view_topic(topic_id):
    page = request.args.get('page', 1, type=int)

    topic = Topic.query.filter_by(id=topic_id).first()
    posts = Post.query.filter_by(topic_id=topic.id).\
        paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    # Count the topic views
    topic.views += 1

    # Update the topicsread status if the user hasn't read it
    forumsread = None
    if current_user.is_authenticated():
        forumsread = ForumsRead.query.\
            filter_by(user_id=current_user.id,
                      forum_id=topic.forum.id).first()

    topic.update_read(current_user, topic.forum, forumsread)
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


@forum.route("/topic/<int:topic_id>/move/<int:forum_id>")
@login_required
def move_topic(topic_id, forum_id):
    forum = Forum.query.filter_by(id=forum_id).first_or_404()
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if not topic.move(forum):
        flash("Could not move the topic to forum %s" % forum.title, "danger")
        return redirect(url_for("forum.view_topic", topic_id=topic.id))

    flash("Topic was moved to forum %s" % forum.title, "success")
    return redirect(url_for("forum.view_topic", topic_id=topic.id))


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
        post.modified_by = current_user.username
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


@forum.route("/markread")
@forum.route("/<int:forum_id>/markread")
def markread(forum_id=None):

    if not current_user.is_authenticated():
        flash("You need to be logged in for that feature.", "danger")
        return redirect(url_for("forum.index"))

    # Mark a single forum as read
    if forum_id:
        forum = Forum.query.filter_by(id=forum_id).first_or_404()
        forumsread = ForumsRead.query.filter_by(user_id=current_user.id,
                                                forum_id=forum.id).first()
        TopicsRead.query.filter_by(user_id=current_user.id,
                                   forum_id=forum.id).delete()

        if not forumsread:
            forumsread = ForumsRead()
            forumsread.user_id = current_user.id
            forumsread.forum_id = forum.id

        forumsread.last_read = datetime.datetime.utcnow()
        forumsread.cleared = datetime.datetime.utcnow()

        db.session.add(forumsread)
        db.session.commit()

        return redirect(url_for("forum.view_forum", forum_id=forum.id))

    # Mark all forums as read
    ForumsRead.query.filter_by(user_id=current_user.id).delete()
    TopicsRead.query.filter_by(user_id=current_user.id).delete()

    forums = Forum.query.all()
    forumsread_list = []
    for forum in forums:
        forumsread = ForumsRead()
        forumsread.user_id = current_user.id
        forumsread.forum_id = forum.id
        forumsread.last_read = datetime.datetime.utcnow()
        forumsread.cleared = datetime.datetime.utcnow()
        forumsread_list.append(forumsread)

    db.session.add_all(forumsread_list)
    db.session.commit()

    return redirect(url_for("forum.index"))


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
