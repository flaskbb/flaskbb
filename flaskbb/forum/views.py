# -*- coding: utf-8 -*-
"""
    flaskbb.forum.views
    ~~~~~~~~~~~~~~~~~~~

    This module handles the forum logic like creating and viewing
    topics and posts.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import math
from sqlalchemy import asc, desc
from flask import (Blueprint, redirect, url_for, current_app, request, flash,
                   abort)
from flask_login import login_required, current_user
from flask_babelplus import gettext as _
from flask_allows import Permission, And

from flaskbb.extensions import db, allows
from flaskbb.utils.settings import flaskbb_config
from flaskbb.utils.helpers import (get_online_users, time_diff, time_utcnow,
                                   format_quote, render_template,
                                   do_topic_action)
from flaskbb.utils.requirements import (CanAccessForum, CanAccessTopic,
                                        CanDeletePost, CanDeleteTopic,
                                        CanEditPost, CanPostReply,
                                        CanPostTopic,
                                        IsAtleastModeratorInForum)
from flaskbb.forum.models import (Category, Forum, Topic, Post, ForumsRead,
                                  TopicsRead)
from flaskbb.forum.forms import (NewTopicForm, QuickreplyForm, ReplyForm,
                                 ReportForm, SearchPageForm, UserSearchForm)
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
@allows.requires(CanAccessForum())
def view_forum(forum_id, slug=None):
    page = request.args.get('page', 1, type=int)

    forum_instance, forumsread = Forum.get_forum(
        forum_id=forum_id, user=current_user
    )

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
@allows.requires(CanAccessTopic())
def view_topic(topic_id, slug=None):
    page = request.args.get('page', 1, type=int)

    # Fetch some information about the topic
    topic = Topic.get_topic(topic_id=topic_id, user=current_user)

    # Count the topic views
    topic.views += 1
    topic.save()

    # fetch the posts in the topic
    posts = Post.query.\
        outerjoin(User, Post.user_id == User.id).\
        filter(Post.topic_id == topic.id).\
        add_entity(User).\
        order_by(Post.id.asc()).\
        paginate(page, flaskbb_config['POSTS_PER_PAGE'], False)

    # Abort if there are no posts on this page
    if len(posts.items) == 0:
        abort(404)

    # Update the topicsread status if the user hasn't read it
    forumsread = None
    if current_user.is_authenticated:
        forumsread = ForumsRead.query.\
            filter_by(user_id=current_user.id,
                      forum_id=topic.forum.id).first()

    topic.update_read(current_user, topic.forum, forumsread)

    form = None
    if Permission(CanPostReply):
        form = QuickreplyForm()
        if form.validate_on_submit():
            post = form.save(current_user, topic)
            return view_post(post.id)

    return render_template("forum/topic.html", topic=topic, posts=posts,
                           last_seen=time_diff(), form=form)


@forum.route("/post/<int:post_id>")
def view_post(post_id):
    """Redirects to a post in a topic."""
    post = Post.query.filter_by(id=post_id).first_or_404()
    post_in_topic = Post.query.\
        filter(Post.topic_id == post.topic_id,
               Post.id <= post_id).\
        order_by(Post.id.asc()).\
        count()
    page = math.ceil(post_in_topic / float(flaskbb_config['POSTS_PER_PAGE']))

    return redirect(post.topic.url + "?page=%d#pid%s" % (page, post.id))


@forum.route("/<int:forum_id>/topic/new", methods=["POST", "GET"])
@forum.route("/<int:forum_id>-<slug>/topic/new", methods=["POST", "GET"])
@login_required
def new_topic(forum_id, slug=None):
    forum_instance = Forum.query.filter_by(id=forum_id).first_or_404()

    if not Permission(CanPostTopic):
        flash(_("You do not have the permissions to create a new topic."),
              "danger")
        return redirect(forum_instance.url)

    form = NewTopicForm()
    if request.method == "POST":
        if "preview" in request.form and form.validate():
            return render_template(
                "forum/new_topic.html", forum=forum_instance,
                form=form, preview=form.content.data
            )
        if "submit" in request.form and form.validate():
            topic = form.save(current_user, forum_instance)
            # redirect to the new topic
            return redirect(url_for('forum.view_topic', topic_id=topic.id))

    return render_template(
        "forum/new_topic.html", forum=forum_instance, form=form
    )


@forum.route("/topic/<int:topic_id>/delete", methods=["POST"])
@forum.route("/topic/<int:topic_id>-<slug>/delete", methods=["POST"])
@login_required
def delete_topic(topic_id=None, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if not Permission(CanDeleteTopic):
        flash(_("You do not have the permissions to delete this topic."),
              "danger")
        return redirect(topic.forum.url)

    involved_users = User.query.filter(Post.topic_id == topic.id,
                                       User.id == Post.user_id).all()
    topic.delete(users=involved_users)
    return redirect(url_for("forum.view_forum", forum_id=topic.forum_id))


@forum.route("/topic/<int:topic_id>/lock", methods=["POST"])
@forum.route("/topic/<int:topic_id>-<slug>/lock", methods=["POST"])
@login_required
def lock_topic(topic_id=None, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if not Permission(IsAtleastModeratorInForum(forum=topic.forum)):
        flash(_("You do not have the permissions to lock this topic."),
              "danger")
        return redirect(topic.url)

    topic.locked = True
    topic.save()
    return redirect(topic.url)


@forum.route("/topic/<int:topic_id>/unlock", methods=["POST"])
@forum.route("/topic/<int:topic_id>-<slug>/unlock", methods=["POST"])
@login_required
def unlock_topic(topic_id=None, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if not Permission(IsAtleastModeratorInForum(forum=topic.forum)):
        flash(_("You do not have the permissions to unlock this topic."),
              "danger")
        return redirect(topic.url)

    topic.locked = False
    topic.save()
    return redirect(topic.url)


@forum.route("/topic/<int:topic_id>/highlight", methods=["POST"])
@forum.route("/topic/<int:topic_id>-<slug>/highlight", methods=["POST"])
@login_required
def highlight_topic(topic_id=None, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if not Permission(IsAtleastModeratorInForum(forum=topic.forum)):
        flash(_("You do not have the permissions to highlight this topic."),
              "danger")
        return redirect(topic.url)

    topic.important = True
    topic.save()
    return redirect(topic.url)


@forum.route("/topic/<int:topic_id>/trivialize", methods=["POST"])
@forum.route("/topic/<int:topic_id>-<slug>/trivialize", methods=["POST"])
@login_required
def trivialize_topic(topic_id=None, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    # Unlock is basically the same as lock
    if not Permission(IsAtleastModeratorInForum(forum=topic.forum)):
        flash(_("You do not have the permissions to trivialize this topic."),
              "danger")
        return redirect(topic.url)

    topic.important = False
    topic.save()
    return redirect(topic.url)


@forum.route("/forum/<int:forum_id>/edit", methods=["POST", "GET"])
@forum.route("/forum/<int:forum_id>-<slug>/edit", methods=["POST", "GET"])
@login_required
def manage_forum(forum_id, slug=None):
    page = request.args.get('page', 1, type=int)

    forum_instance, forumsread = Forum.get_forum(forum_id=forum_id,
                                                 user=current_user)

    # remove the current forum from the select field (move).
    available_forums = Forum.query.order_by(Forum.position).all()
    available_forums.remove(forum_instance)

    if not Permission(IsAtleastModeratorInForum(forum=forum_instance)):
        flash(_("You do not have the permissions to moderate this forum."),
              "danger")
        return redirect(forum_instance.url)

    if forum_instance.external:
        return redirect(forum_instance.external)

    topics = Forum.get_topics(
        forum_id=forum_instance.id, user=current_user, page=page,
        per_page=flaskbb_config["TOPICS_PER_PAGE"]
    )

    mod_forum_url = url_for("forum.manage_forum", forum_id=forum_instance.id,
                            slug=forum_instance.slug)

    # the code is kind of the same here but it somehow still looks cleaner than
    # doin some magic
    if request.method == "POST":
        ids = request.form.getlist("rowid")
        tmp_topics = Topic.query.filter(Topic.id.in_(ids)).all()

        if not len(tmp_topics) > 0:
            flash(_("In order to perform this action you have to select at "
                    "least one topic."), "danger")
            return redirect(mod_forum_url)

        # locking/unlocking
        if "lock" in request.form:
            changed = do_topic_action(topics=tmp_topics, user=current_user,
                                      action="locked", reverse=False)

            flash(_("%(count)s topics locked.", count=changed), "success")
            return redirect(mod_forum_url)

        elif "unlock" in request.form:
            changed = do_topic_action(topics=tmp_topics, user=current_user,
                                      action="locked", reverse=True)
            flash(_("%(count)s topics unlocked.", count=changed), "success")
            return redirect(mod_forum_url)

        # highlighting/trivializing
        elif "highlight" in request.form:
            changed = do_topic_action(topics=tmp_topics, user=current_user,
                                      action="important", reverse=False)
            flash(_("%(count)s topics highlighted.", count=changed), "success")
            return redirect(mod_forum_url)

        elif "trivialize" in request.form:
            changed = do_topic_action(topics=tmp_topics, user=current_user,
                                      action="important", reverse=True)
            flash(_("%(count)s topics trivialized.", count=changed), "success")
            return redirect(mod_forum_url)

        # deleting
        elif "delete" in request.form:
            changed = do_topic_action(topics=tmp_topics, user=current_user,
                                      action="delete", reverse=False)
            flash(_("%(count)s topics deleted.", count=changed), "success")
            return redirect(mod_forum_url)

        # moving
        elif "move" in request.form:
            new_forum_id = request.form.get("forum")

            if not new_forum_id:
                flash(_("Please choose a new forum for the topics."), "info")
                return redirect(mod_forum_url)

            new_forum = Forum.query.filter_by(id=new_forum_id).first_or_404()
            # check the permission in the current forum and in the new forum

            if not Permission(
                And(
                    IsAtleastModeratorInForum(forum_id=new_forum_id),
                    IsAtleastModeratorInForum(forum=forum_instance)
                )
            ):
                flash(_("You do not have the permissions to move this topic."),
                      "danger")
                return redirect(mod_forum_url)

            new_forum.move_topics_to(tmp_topics)
            return redirect(mod_forum_url)

    return render_template(
        "forum/edit_forum.html", forum=forum_instance, topics=topics,
        available_forums=available_forums, forumsread=forumsread,
    )


@forum.route("/topic/<int:topic_id>/post/new", methods=["POST", "GET"])
@forum.route("/topic/<int:topic_id>-<slug>/post/new", methods=["POST", "GET"])
@login_required
def new_post(topic_id, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()

    if not Permission(CanPostReply):
        flash(_("You do not have the permissions to post in this topic."),
              "danger")
        return redirect(topic.forum.url)

    form = ReplyForm()
    if form.validate_on_submit():
        if "preview" in request.form:
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

    if not Permission(CanPostReply):
        flash(_("You do not have the permissions to post in this topic."),
              "danger")
        return view_post(post.id)

    form = ReplyForm()
    if form.validate_on_submit():
        if "preview" in request.form:
            return render_template(
                "forum/new_post.html", topic=topic,
                form=form, preview=form.content.data
            )
        else:
            post = form.save(current_user, topic)
            return view_post(post.id)
    else:
        form.content.data = format_quote(post.username, post.content)

    return render_template("forum/new_post.html", topic=post.topic, form=form)


@forum.route("/post/<int:post_id>/edit", methods=["POST", "GET"])
@login_required
def edit_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()

    if not Permission(CanEditPost):
        flash(_("You do not have the permissions to edit this post."),
              "danger")
        return view_post(post.id)

    if post.first_post:
        form = NewTopicForm()
    else:
        form = ReplyForm()

    if form.validate_on_submit():
        if "preview" in request.form:
            return render_template(
                "forum/new_post.html", topic=post.topic,
                form=form, preview=form.content.data, edit_mode=True
            )
        else:
            form.populate_obj(post)
            post.date_modified = time_utcnow()
            post.modified_by = current_user.username
            post.save()

            if post.first_post:
                post.topic.title = form.title.data
                post.topic.save()
            return view_post(post.id)
    else:
        if post.first_post:
            form.title.data = post.topic.title

        form.content.data = post.content

    return render_template("forum/new_post.html", topic=post.topic, form=form,
                           edit_mode=True)


@forum.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()

    # TODO: Bulk delete

    if not Permission(CanDeletePost):
        flash(_("You do not have the permissions to delete this post."),
              "danger")
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
        flash(_("Thanks for reporting."), "success")

    return render_template("forum/report_post.html", form=form)


@forum.route("/post/<int:post_id>/raw", methods=["POST", "GET"])
@login_required
def raw_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    return format_quote(username=post.username, content=post.content)


@forum.route("/<int:forum_id>/markread", methods=["POST"])
@forum.route("/<int:forum_id>-<slug>/markread", methods=["POST"])
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

        forumsread.last_read = time_utcnow()
        forumsread.cleared = time_utcnow()

        db.session.add(forumsread)
        db.session.commit()

        flash(_("Forum %(forum)s marked as read.", forum=forum_instance.title),
              "success")

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
        forumsread.last_read = time_utcnow()
        forumsread.cleared = time_utcnow()
        forumsread_list.append(forumsread)

    db.session.add_all(forumsread_list)
    db.session.commit()

    flash(_("All forums marked as read."), "success")

    return redirect(url_for("forum.index"))


@forum.route("/who-is-online")
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
    sort_by = request.args.get('sort_by', 'reg_date')
    order_by = request.args.get('order_by', 'asc')

    sort_obj = None
    order_func = None
    if order_by == 'asc':
        order_func = asc
    else:
        order_func = desc

    if sort_by == 'reg_date':
        sort_obj = User.id
    elif sort_by == 'post_count':
        sort_obj = User.post_count
    else:
        sort_obj = User.username

    search_form = UserSearchForm()
    if search_form.validate():
        users = search_form.get_results().\
            paginate(page, flaskbb_config['USERS_PER_PAGE'], False)
        return render_template("forum/memberlist.html", users=users,
                               search_form=search_form)
    else:
        users = User.query.order_by(order_func(sort_obj)).\
            paginate(page, flaskbb_config['USERS_PER_PAGE'], False)
        return render_template("forum/memberlist.html", users=users,
                               search_form=search_form)


@forum.route("/topictracker", methods=["GET", "POST"])
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

    # bulk untracking
    if request.method == "POST":
        topic_ids = request.form.getlist("rowid")
        tmp_topics = Topic.query.filter(Topic.id.in_(topic_ids)).all()

        for topic in tmp_topics:
            current_user.untrack_topic(topic)
        current_user.save()

        flash(_("%(topic_count)s topics untracked.",
                topic_count=len(tmp_topics)), "success")
        return redirect(url_for("forum.topictracker"))

    return render_template("forum/topictracker.html", topics=topics)


@forum.route("/topictracker/<int:topic_id>/add", methods=["POST"])
@forum.route("/topictracker/<int:topic_id>-<slug>/add", methods=["POST"])
@login_required
def track_topic(topic_id, slug=None):
    topic = Topic.query.filter_by(id=topic_id).first_or_404()
    current_user.track_topic(topic)
    current_user.save()
    return redirect(topic.url)


@forum.route("/topictracker/<int:topic_id>/delete", methods=["POST"])
@forum.route("/topictracker/<int:topic_id>-<slug>/delete", methods=["POST"])
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
