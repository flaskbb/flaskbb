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

from flask import (Blueprint, redirect, url_for, current_app,
                   request, flash)
from flask.ext.login import login_required, current_user

from flaskbb.extensions import db
from flaskbb.utils.settings import flaskbb_config
from flaskbb.utils.helpers import (get_online_users, time_diff, render_template,
                                   format_quote)
from flaskbb.utils.permissions import (can_post_reply, can_post_topic,
                                       can_delete_topic, can_delete_post,
                                       can_edit_post, can_moderate)
from flaskbb.forum.models import (Category, Forum, Topic, Post, ForumsRead,
                                  TopicsRead)
from flaskbb.forum.forms import (QuickreplyForm, ReplyForm, NewTopicForm,
                                 ReportForm, UserSearchForm, SearchPageForm)
from flaskbb.user.models import User

forum = Blueprint("forum", __name__)


@forum.route("/")
def index():
    categories = Category.get_all(user=current_user)

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
@forum.route("/category/<int:category_id>-<slug>")
def view_category(category_id, slug=None):
    category, forums = Category.\
        get_forums(category_id=category_id, user=current_user)

    return render_template("forum/category.html", forums=forums,
                           category=category)


@forum.route("/forum/<int:forum_id>")
@forum.route("/forum/<int:forum_id>-<slug>")
def view_forum(forum_id, slug=None):
    page = request.args.get('page', 1, type=int)

    forum_instance, forumsread = Forum.get_forum(forum_id=forum_id,
                                                 user=current_user)

    if forum_instance.external:
        return redirect(forum_instance.external)

    topics = Forum.get_topics(
        forum_id=forum_instance.id, user=current_user, page=page,
        per_page=flaskbb_config["TOPICS_PER_PAGE"]
    )

    return render_template(
        "forum/forum.html", forum=forum_instance,
        topics=topics, forumsread=forumsread,
    )


@forum.route("/topic/<int:topic_id>", methods=["POST", "GET"])
@forum.route("/topic/<int:topic_id>-<slug>", methods=["POST", "GET"])
def view_topic(topic_id, slug=None):
    page = request.args.get('page', 1, type=int)

    # Fetch some information about the topic
    topic = Topic.query.filter_by(id=topic_id).first()

    # Count the topic views
    topic.views += 1
    topic.save()

    # fetch the posts in the topic
    posts = Post.query.\
        join(User, Post.user_id == User.id).\
        filter(Post.topic_id == topic.id).\
        add_entity(User).\
        order_by(Post.id.asc()).\
        paginate(page, flaskbb_config['POSTS_PER_PAGE'], False)

    # Update the topicsread status if the user hasn't read it
    forumsread = None
    if current_user.is_authenticated():
        forumsread = ForumsRead.query.\
            filter_by(user_id=current_user.id,
                      forum_id=topic.forum.id).first()

    topic.update_read(current_user, topic.forum, forumsread)

    form = None

    if can_post_reply(user=current_user, topic=topic):
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
    page = count / flaskbb_config["POSTS_PER_PAGE"]

    if count > flaskbb_config["POSTS_PER_PAGE"]:
        page += 1
    else:
        page = 1

    return redirect(post.topic.url + "?page=%d#pid%s" % (page, post.id))


@forum.route("/<int:forum_id>/topic/new", methods=["POST", "GET"])
@forum.route("/<int:forum_id>-<slug>/topic/new", methods=["POST", "GET"])
@login_required
def new_topic(forum_id, slug=None):
    forum_instance = Forum.query.filter_by(id=forum_id).first_or_404()

    if not can_post_topic(user=current_user, forum=forum):
        flash("You do not have the permissions to create a new topic.",
              "danger")
        return redirect(forum.url)

    form = NewTopicForm()
    if form.validate_on_submit():
        if request.form['button'] == 'preview':
            return render_template(
                "forum/new_topic.html", forum=forum_instance,
                form=form, preview=form.content.data
            )
        else:
            topic = form.save(current_user, forum_instance)

            # redirect to the new topic
            return redirect(url_for('forum.view_topic', topic_id=topic.id))
    return render_template(
        "forum/new_topic.html", forum=forum_instance, form=form
    )


@forum.route("/topic/<int:topic_id>/delete")
@forum.route("/topic/<int:topic_id>-<slug>/delete")
@login_required
def delete_topic(topic_id, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if not can_delete_topic(user=current_user, topic=topic):

        flash("You do not have the permissions to delete the topic", "danger")
        return redirect(topic.forum.url)

    involved_users = User.query.filter(Post.topic_id == topic.id,
                                       User.id == Post.user_id).all()
    topic.delete(users=involved_users)
    return redirect(url_for("forum.view_forum", forum_id=topic.forum_id))


@forum.route("/topic/<int:topic_id>/lock")
@forum.route("/topic/<int:topic_id>-<slug>/lock")
@login_required
def lock_topic(topic_id, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    # TODO: Bulk lock

    if not can_moderate(user=current_user, forum=topic.forum):
        flash("You do not have the permissions to lock this topic", "danger")
        return redirect(topic.url)

    topic.locked = True
    topic.save()
    return redirect(topic.url)


@forum.route("/topic/<int:topic_id>/unlock")
@forum.route("/topic/<int:topic_id>-<slug>/unlock")
@login_required
def unlock_topic(topic_id, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    # TODO: Bulk unlock

    # Unlock is basically the same as lock
    if not can_moderate(user=current_user, forum=topic.forum):
        flash("Yo do not have the permissions to unlock this topic", "danger")
        return redirect(topic.url)

    topic.locked = False
    topic.save()
    return redirect(topic.url)


@forum.route("/topic/<int:topic_id>/move/<int:forum_id>")
@forum.route(
    "/topic/<int:topic_id>-<topic_slug>/move/<int:forum_id>-<forum_slug>"
)
@login_required
def move_topic(topic_id, forum_id, topic_slug=None, forum_slug=None):
    forum_instance = Forum.query.filter_by(id=forum_id).first_or_404()
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    # TODO: Bulk move

    if not can_moderate(user=current_user, forum=topic.forum):
        flash("Yo do not have the permissions to move this topic", "danger")
        return redirect(forum_instance.url)

    if not topic.move(forum_instance):
        flash(
            "Could not move the topic to forum %s" % forum_instance.title,
            "danger"
        )
        return redirect(topic.url)

    flash("Topic was moved to forum %s" % forum_instance.title, "success")
    return redirect(topic.url)


@forum.route("/topic/<int:old_id>/merge/<int:new_id>")
@forum.route("/topic/<int:old_id>-<old_slug>/merge/<int:new_id>-<new_slug>")
@login_required
def merge_topic(old_id, new_id, old_slug=None, new_slug=None):
    _old_topic = Topic.query.filter_by(id=old_id).first_or_404()
    _new_topic = Topic.query.filter_by(id=new_id).first_or_404()

    # TODO: Bulk merge

    # Looks to me that the user should have permissions on both forums, right?
    if not can_moderate(user=current_user, forum=_old_topic.forum):
        flash("Yo do not have the permissions to merge this topic", "danger")
        return redirect(_old_topic.url)

    if not _old_topic.merge(_new_topic):
        flash("Could not merge the topic.", "danger")
        return redirect(_old_topic.url)

    flash("Topic succesfully merged.", "success")
    return redirect(_new_topic.url)


@forum.route("/topic/<int:topic_id>/post/new", methods=["POST", "GET"])
@forum.route("/topic/<int:topic_id>-<slug>/post/new", methods=["POST", "GET"])
@login_required
def new_post(topic_id, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if not can_post_reply(user=current_user, topic=topic):
        flash("You do not have the permissions to post here", "danger")
        return redirect(topic.forum.url)

    form = ReplyForm()
    if form.validate_on_submit():
        if request.form['button'] == 'preview':
            return render_template(
                "forum/new_post.html", topic=topic,
                form=form, preview=form.content.data
            )
        else:
            post = form.save(current_user, topic)
            return view_post(post.id)

    return render_template("forum/new_post.html", topic=topic, form=form)


@forum.route(
    "/topic/<int:topic_id>/post/<int:post_id>/reply", methods=["POST", "GET"]
)
@login_required
def reply_post(topic_id, post_id):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()
    post = Post.query.filter_by(id=post_id).first_or_404()

    if not can_post_reply(user=current_user, topic=topic):
        flash("You do not have the permissions to post in this topic", "danger")
        return redirect(topic.forum.url)

    form = ReplyForm()
    if form.validate_on_submit():
        if request.form['button'] == 'preview':
            return render_template(
                "forum/new_post.html", topic=topic,
                form=form, preview=form.content.data
            )
        else:
            form.save(current_user, topic)
            return redirect(post.topic.url)
    else:
        form.content.data = format_quote(post)

    return render_template("forum/new_post.html", topic=post.topic, form=form)


@forum.route("/post/<int:post_id>/edit", methods=["POST", "GET"])
@login_required
def edit_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()

    if not can_edit_post(user=current_user, post=post):
        flash("You do not have the permissions to edit this post", "danger")
        return redirect(post.topic.url)

    form = ReplyForm()
    if form.validate_on_submit():
        if request.form['button'] == 'preview':
            return render_template(
                "forum/new_post.html", topic=post.topic,
                form=form, preview=form.content.data
            )
        else:
            form.populate_obj(post)
            post.date_modified = datetime.datetime.utcnow()
            post.modified_by = current_user.username
            post.save()
            return redirect(post.topic.url)
    else:
        form.content.data = post.content

    return render_template("forum/new_post.html", topic=post.topic, form=form)


@forum.route("/post/<int:post_id>/delete")
@login_required
def delete_post(post_id, slug=None):
    post = Post.query.filter_by(id=post_id).first_or_404()

    # TODO: Bulk delete

    if not can_delete_post(user=current_user, post=post):
        flash("You do not have the permissions to edit this post", "danger")
        return redirect(post.topic.url)

    first_post = post.first_post
    topic_url = post.topic.url
    forum_url = post.topic.forum.url

    post.delete()

    # If the post was the first post in the topic, redirect to the forums
    if first_post:
        return redirect(forum_url)
    return redirect(topic_url)


@forum.route("/post/<int:post_id>/report", methods=["GET", "POST"])
@login_required
def report_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()

    form = ReportForm()
    if form.validate_on_submit():
        form.save(current_user, post)
        flash("Thanks for reporting!", "success")

    return render_template("forum/report_post.html", form=form)


@forum.route("/post/<int:post_id>/raw", methods=["POST", "GET"])
@login_required
def raw_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    return format_quote(post)


@forum.route("/markread")
@forum.route("/<int:forum_id>/markread")
@forum.route("/<int:forum_id>-<slug>/markread")
@login_required
def markread(forum_id=None, slug=None):
    # Mark a single forum as read
    if forum_id:
        forum_instance = Forum.query.filter_by(id=forum_id).first_or_404()
        forumsread = ForumsRead.query.filter_by(
            user_id=current_user.id, forum_id=forum_instance.id
        ).first()
        TopicsRead.query.filter_by(user_id=current_user.id,
                                   forum_id=forum_instance.id).delete()

        if not forumsread:
            forumsread = ForumsRead()
            forumsread.user_id = current_user.id
            forumsread.forum_id = forum_instance.id

        forumsread.last_read = datetime.datetime.utcnow()
        forumsread.cleared = datetime.datetime.utcnow()

        db.session.add(forumsread)
        db.session.commit()

        return redirect(forum_instance.url)

    # Mark all forums as read
    ForumsRead.query.filter_by(user_id=current_user.id).delete()
    TopicsRead.query.filter_by(user_id=current_user.id).delete()

    forums = Forum.query.all()
    forumsread_list = []
    for forum_instance in forums:
        forumsread = ForumsRead()
        forumsread.user_id = current_user.id
        forumsread.forum_id = forum_instance.id
        forumsread.last_read = datetime.datetime.utcnow()
        forumsread.cleared = datetime.datetime.utcnow()
        forumsread_list.append(forumsread)

    db.session.add_all(forumsread_list)
    db.session.commit()

    return redirect(url_for("forum.index"))


@forum.route("/who_is_online")
def who_is_online():
    if current_app.config['REDIS_ENABLED']:
        online_users = get_online_users()
    else:
        online_users = User.query.filter(User.lastseen >= time_diff()).all()
    return render_template("forum/online_users.html",
                           online_users=online_users)


@forum.route("/memberlist", methods=['GET', 'POST'])
def memberlist():
    page = request.args.get('page', 1, type=int)

    search_form = UserSearchForm()

    if search_form.validate():
        users = search_form.get_results().\
            paginate(page, flaskbb_config['USERS_PER_PAGE'], False)
        return render_template("forum/memberlist.html", users=users,
                               search_form=search_form)
    else:
        users = User.query.\
            paginate(page, flaskbb_config['USERS_PER_PAGE'], False)
        return render_template("forum/memberlist.html", users=users,
                               search_form=search_form)


@forum.route("/topictracker")
@login_required
def topictracker():
    page = request.args.get("page", 1, type=int)
    topics = current_user.tracked_topics.\
        outerjoin(TopicsRead,
                  db.and_(TopicsRead.topic_id == Topic.id,
                          TopicsRead.user_id == current_user.id)).\
        add_entity(TopicsRead).\
        order_by(Topic.last_updated.desc()).\
        paginate(page, flaskbb_config['TOPICS_PER_PAGE'], True)

    return render_template("forum/topictracker.html", topics=topics)


@forum.route("/topictracker/<int:topic_id>/add")
@forum.route("/topictracker/<int:topic_id>-<slug>/add")
@login_required
def track_topic(topic_id, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()
    current_user.track_topic(topic)
    current_user.save()
    return redirect(topic.url)


@forum.route("/topictracker/<int:topic_id>/delete")
@forum.route("/topictracker/<int:topic_id>-<slug>/delete")
@login_required
def untrack_topic(topic_id, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()
    current_user.untrack_topic(topic)
    current_user.save()
    return redirect(topic.url)


@forum.route("/search", methods=['GET', 'POST'])
def search():
    form = SearchPageForm()

    if form.validate_on_submit():
        result = form.get_results()
        return render_template('forum/search_result.html', form=form,
                               result=result)

    return render_template('forum/search_form.html', form=form)
