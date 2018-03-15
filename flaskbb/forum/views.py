# -*- coding: utf-8 -*-
'''
    flaskbb.forum.views
    ~~~~~~~~~~~~~~~~~~~

    This module handles the forum logic like creating and viewing
    topics and posts.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
'''
import logging
import math

from flask import (Blueprint, abort, current_app, flash, redirect, request,
                   url_for)
from flask.views import MethodView
from flask_allows import And, Permission
from flask_babelplus import gettext as _
from flask_login import current_user, login_required
from sqlalchemy import asc, desc

from flaskbb.extensions import allows, db
from flaskbb.forum.forms import (NewTopicForm, QuickreplyForm, ReplyForm,
                                 ReportForm, SearchPageForm, UserSearchForm)
from flaskbb.forum.models import (Category, Forum, ForumsRead, Post, Topic,
                                  TopicsRead)
from flaskbb.user.models import User
from flaskbb.utils.helpers import (do_topic_action, format_quote,
                                   get_online_users, real, register_view,
                                   render_template, time_diff, time_utcnow)
from flaskbb.utils.requirements import (CanAccessForum, CanAccessTopic,
                                        CanDeletePost, CanDeleteTopic,
                                        CanEditPost, CanPostReply,
                                        CanPostTopic, Has,
                                        IsAtleastModeratorInForum)
from flaskbb.utils.settings import flaskbb_config

logger = logging.getLogger(__name__)


forum = Blueprint("forum", __name__)


class ForumIndex(MethodView):

    def get(self):
        categories = Category.get_all(user=real(current_user))

        # Fetch a few stats about the forum
        user_count = User.query.count()
        topic_count = Topic.query.count()
        post_count = Post.query.count()
        newest_user = User.query.order_by(User.id.desc()).first()

        # Check if we use redis or not
        if not current_app.config['REDIS_ENABLED']:
            online_users = User.query.filter(User.lastseen >= time_diff()).count()

            # Because we do not have server side sessions, we cannot check if there
            # are online guests
            online_guests = None
        else:
            online_users = len(get_online_users())
            online_guests = len(get_online_users(guest=True))

        return render_template(
            'forum/index.html',
            categories=categories,
            user_count=user_count,
            topic_count=topic_count,
            post_count=post_count,
            newest_user=newest_user,
            online_users=online_users,
            online_guests=online_guests
        )


class ViewCategory(MethodView):

    def get(self, category_id, slug=None):
        category, forums = Category.get_forums(category_id=category_id, user=real(current_user))

        return render_template('forum/category.html', forums=forums, category=category)


class ViewForum(MethodView):
    decorators = [allows.requires(CanAccessForum())]

    def get(self, forum_id, slug=None):
        page = request.args.get('page', 1, type=int)

        forum_instance, forumsread = Forum.get_forum(forum_id=forum_id, user=real(current_user))

        if forum_instance.external:
            return redirect(forum_instance.external)

        topics = Forum.get_topics(
            forum_id=forum_instance.id,
            user=real(current_user),
            page=page,
            per_page=flaskbb_config['TOPICS_PER_PAGE']
        )

        return render_template(
            'forum/forum.html',
            forum=forum_instance,
            topics=topics,
            forumsread=forumsread,
        )


class ViewPost(MethodView):

    def get(self, post_id):
        '''Redirects to a post in a topic.'''
        post = Post.query.filter_by(id=post_id).first_or_404()
        post_in_topic = Post.query.filter(Post.topic_id == post.topic_id,
                                          Post.id <= post_id).order_by(Post.id.asc()).count()
        page = int(math.ceil(post_in_topic / float(flaskbb_config['POSTS_PER_PAGE'])))

        return redirect(
            url_for(
                'forum.view_topic',
                topic_id=post.topic.id,
                slug=post.topic.slug,
                page=page,
                _anchor='pid{}'.format(post.id)
            )
        )


class ViewTopic(MethodView):
    decorators = [allows.requires(CanAccessTopic())]

    def get(self, topic_id, slug=None):
        page = request.args.get('page', 1, type=int)

        # Fetch some information about the topic
        topic = Topic.get_topic(topic_id=topic_id, user=real(current_user))

        # Count the topic views
        topic.views += 1
        topic.save()


        # Update the topicsread status if the user hasn't read it
        forumsread = None
        if current_user.is_authenticated:
            forumsread = ForumsRead.query.\
                filter_by(user_id=current_user.id,
                          forum_id=topic.forum_id).first()

        topic.update_read(real(current_user), topic.forum, forumsread)

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

        return render_template(
            'forum/topic.html', topic=topic, posts=posts, last_seen=time_diff(), form=self.form()
        )

    @allows.requires(CanPostReply)
    def post(self, topic_id, slug=None):
        topic = Topic.get_topic(topic_id=topic_id, user=real(current_user))
        form = self.form()

        if not form:
            flash(_('Cannot post reply'), 'warning')
            return redirect('forum.view_topic', topic_id=topic_id, slug=slug)

        elif form.validate_on_submit():
            post = form.save(real(current_user), topic)
            return redirect(url_for('forum.view_post', post_id=post.id))

        else:
            for e in form.errors.get('content', []):
                flash(e, 'danger')
            return redirect(url_for('forum.view_topic', topic_id=topic_id, slug=slug))

    def form(self):
        if Permission(CanPostReply):
            return QuickreplyForm()
        return None


class NewTopic(MethodView):
    decorators = [login_required]
    form = NewTopicForm

    def get(self, forum_id, slug=None):
        forum_instance = Forum.query.filter_by(id=forum_id).first_or_404()
        return render_template('forum/new_topic.html', forum=forum_instance, form=self.form())

    @allows.requires(CanPostTopic)
    def post(self, forum_id, slug=None):
        forum_instance = Forum.query.filter_by(id=forum_id).first_or_404()
        form = self.form()
        if 'preview' in request.form and form.validate():
            return render_template(
                'forum/new_topic.html', forum=forum_instance, form=form, preview=form.content.data
            )
        elif 'submit' in request.form and form.validate():
            topic = form.save(real(current_user), forum_instance)
            # redirect to the new topic
            return redirect(url_for('forum.view_topic', topic_id=topic.id))
        else:
            return render_template('forum/new_topic.html', forum=forum_instance, form=form)


class ManageForum(MethodView):
    decorators = [allows.requires(IsAtleastModeratorInForum()), login_required]

    def get(self, forum_id, slug=None):

        forum_instance, forumsread = Forum.get_forum(forum_id=forum_id, user=real(current_user))

        if forum_instance.external:
            return redirect(forum_instance.external)

        # remove the current forum from the select field (move).
        available_forums = Forum.query.order_by(Forum.position).all()
        available_forums.remove(forum_instance)
        page = request.args.get('page', 1, type=int)
        topics = Forum.get_topics(
            forum_id=forum_instance.id,
            user=real(current_user),
            page=page,
            per_page=flaskbb_config['TOPICS_PER_PAGE']
        )

        return render_template(
            'forum/edit_forum.html',
            forum=forum_instance,
            topics=topics,
            available_forums=available_forums,
            forumsread=forumsread,
        )

    def post(self, forum_id, slug=None):
        forum_instance, __ = Forum.get_forum(forum_id=forum_id, user=real(current_user))
        mod_forum_url = url_for(
            'forum.manage_forum', forum_id=forum_instance.id, slug=forum_instance.slug
        )

        ids = request.form.getlist('rowid')
        tmp_topics = Topic.query.filter(Topic.id.in_(ids)).all()

        if not len(tmp_topics) > 0:
            flash(
                _('In order to perform this action you have to select at '
                  'least one topic.'), 'danger'
            )
            return redirect(mod_forum_url)

        # locking/unlocking
        if 'lock' in request.form:
            changed = do_topic_action(
                topics=tmp_topics, user=real(current_user), action='locked', reverse=False
            )

            flash(_('%(count)s topics locked.', count=changed), 'success')
            return redirect(mod_forum_url)

        elif 'unlock' in request.form:
            changed = do_topic_action(
                topics=tmp_topics, user=real(current_user), action='locked', reverse=True
            )
            flash(_('%(count)s topics unlocked.', count=changed), 'success')
            return redirect(mod_forum_url)

        # highlighting/trivializing
        elif 'highlight' in request.form:
            changed = do_topic_action(
                topics=tmp_topics, user=real(current_user), action='important', reverse=False
            )
            flash(_('%(count)s topics highlighted.', count=changed), 'success')
            return redirect(mod_forum_url)

        elif 'trivialize' in request.form:
            changed = do_topic_action(
                topics=tmp_topics, user=real(current_user), action='important', reverse=True
            )
            flash(_('%(count)s topics trivialized.', count=changed), 'success')
            return redirect(mod_forum_url)

        # deleting
        elif 'delete' in request.form:
            changed = do_topic_action(
                topics=tmp_topics, user=real(current_user), action='delete', reverse=False
            )
            flash(_('%(count)s topics deleted.', count=changed), 'success')
            return redirect(mod_forum_url)

        # moving
        elif 'move' in request.form:
            new_forum_id = request.form.get('forum')

            if not new_forum_id:
                flash(_('Please choose a new forum for the topics.'), 'info')
                return redirect(mod_forum_url)

            new_forum = Forum.query.filter_by(id=new_forum_id).first_or_404()
            # check the permission in the current forum and in the new forum

            if not Permission(And(IsAtleastModeratorInForum(forum_id=new_forum_id),
                                  IsAtleastModeratorInForum(forum=forum_instance))):
                flash(_('You do not have the permissions to move this topic.'), 'danger')
                return redirect(mod_forum_url)

            if new_forum.move_topics_to(tmp_topics):
                flash(_('Topics moved.'), 'success')
            else:
                flash(_('Failed to move topics.'), 'danger')

            return redirect(mod_forum_url)

        # hiding/unhiding
        elif "hide" in request.form:
            changed = do_topic_action(
                topics=tmp_topics, user=real(current_user), action="hide", reverse=False
            )
            flash(_("%(count)s topics hidden.", count=changed), "success")
            return redirect(mod_forum_url)

        elif "unhide" in request.form:
            changed = do_topic_action(
                topics=tmp_topics, user=real(current_user), action="unhide", reverse=False
            )
            flash(_("%(count)s topics unhidden.", count=changed), "success")
            return redirect(mod_forum_url)

        else:
            flash(_('Unknown action requested'), 'danger')
            return redirect(mod_forum_url)


class NewPost(MethodView):
    decorators = [allows.requires(CanPostReply), login_required]

    def get(self, topic_id, slug=None):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()

        return render_template(
            'forum/new_post.html', topic=topic, form=self.form()
        )

    def post(self, topic_id, slug=None):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()

        form = self.form()

        if form.validate_on_submit():
            if 'preview' in request.form:
                return render_template(
                    'forum/new_post.html', topic=topic, form=form,
                    preview=form.content.data
                )
            else:
                post = form.save(real(current_user), topic)
                return redirect(url_for('forum.view_post', post_id=post.id))

        return render_template('forum/new_post.html', topic=topic, form=form)

    def form(self):
        current_app.pluggy.hook.flaskbb_form_new_post(form=ReplyForm)
        return ReplyForm()


class ReplyPost(MethodView):
    decorators = [allows.requires(CanPostReply), login_required]
    form = ReplyForm

    def get(self, topic_id, post_id):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        return render_template('forum/new_post.html', topic=topic, form=self.form())

    def post(self, topic_id, post_id):
        form = self.form()
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        if form.validate_on_submit():
            if 'preview' in request.form:
                return render_template(
                    'forum/new_post.html', topic=topic, form=form, preview=form.content.data
                )
            else:
                post = form.save(real(current_user), topic)
                return redirect(url_for('forum.view_post', post_id=post.id))
        else:
            form.content.data = format_quote(post.username, post.content)

        return render_template('forum/new_post.html', topic=post.topic, form=form)


class EditPost(MethodView):
    decorators = [allows.requires(CanEditPost), login_required]
    form = ReplyForm

    def get(self, post_id):
        post = Post.query.filter_by(id=post_id).first_or_404()
        form = self.form(obj=post)
        return render_template('forum/new_post.html', topic=post.topic, form=form, edit_mode=True)

    def post(self, post_id):
        post = Post.query.filter_by(id=post_id).first_or_404()
        form = self.form(obj=post)

        if form.validate_on_submit():
            if 'preview' in request.form:
                return render_template(
                    'forum/new_post.html',
                    topic=post.topic,
                    form=form,
                    preview=form.content.data,
                    edit_mode=True
                )
            else:
                form.populate_obj(post)
                post.date_modified = time_utcnow()
                post.modified_by = real(current_user).username
                post.save()
                return redirect(url_for('forum.view_post', post_id=post.id))

        return render_template('forum/new_post.html', topic=post.topic, form=form, edit_mode=True)


class ReportView(MethodView):
    decorators = [login_required]
    form = ReportForm

    def get(self, post_id):
        return render_template('forum/report_post.html', form=self.form())

    def post(self, post_id):
        form = self.form()
        if form.validate_on_submit():
            post = Post.query.filter_by(id=post_id).first_or_404()
            form.save(real(current_user), post)
            flash(_('Thanks for reporting.'), 'success')

        return render_template('forum/report_post.html', form=form)


class MemberList(MethodView):
    form = UserSearchForm

    def get(self):
        page = request.args.get('page', 1, type=int)
        sort_by = request.args.get('sort_by', 'reg_date')
        order_by = request.args.get('order_by', 'asc')

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

        users = User.query.order_by(order_func(sort_obj)).paginate(
            page, flaskbb_config['USERS_PER_PAGE'], False
        )
        return render_template('forum/memberlist.html', users=users, search_form=self.form())

    def post(self):
        page = request.args.get('page', 1, type=int)
        sort_by = request.args.get('sort_by', 'reg_date')
        order_by = request.args.get('order_by', 'asc')

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

        form = self.form()
        if form.validate():
            users = form.get_results().paginate(page, flaskbb_config['USERS_PER_PAGE'], False)
            return render_template('forum/memberlist.html', users=users, search_form=form)

        users = User.query.order_by(order_func(sort_obj)).paginate(
            page, flaskbb_config['USERS_PER_PAGE'], False
        )
        return render_template('forum/memberlist.html', users=users, search_form=form)


class TopicTracker(MethodView):
    decorators = [login_required]

    def get(self):
        page = request.args.get('page', 1, type=int)
        topics = real(current_user).tracked_topics.outerjoin(
            TopicsRead,
            db.and_(TopicsRead.topic_id == Topic.id, TopicsRead.user_id == real(current_user).id)
        ).add_entity(TopicsRead).order_by(Topic.last_updated.desc()).paginate(
            page, flaskbb_config['TOPICS_PER_PAGE'], True
        )

        return render_template('forum/topictracker.html', topics=topics)

    def post(self):
        topic_ids = request.form.getlist('rowid')
        tmp_topics = Topic.query.filter(Topic.id.in_(topic_ids)).all()

        for topic in tmp_topics:
            real(current_user).untrack_topic(topic)

        real(current_user).save()

        flash(_('%(topic_count)s topics untracked.', topic_count=len(tmp_topics)), 'success')
        return redirect(url_for('forum.topictracker'))


class Search(MethodView):
    form = SearchPageForm

    def get(self):
        return render_template('forum/search_form.html', form=self.form())

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            result = form.get_results()
            return render_template('forum/search_result.html', form=form, result=result)

        return render_template('forum/search_form.html', form=form)


class DeleteTopic(MethodView):
    decorators = [allows.requires(CanDeleteTopic), login_required]

    def post(self, topic_id, slug=None):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        involved_users = User.query.filter(Post.topic_id == topic.id,
                                           User.id == Post.user_id).all()
        topic.delete(users=involved_users)
        return redirect(url_for('forum.view_forum', forum_id=topic.forum_id))


class LockTopic(MethodView):
    decorators = [allows.requires(IsAtleastModeratorInForum()), login_required]

    def post(self, topic_id, slug=None):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        topic.locked = True
        topic.save()
        return redirect(topic.url)


class UnlockTopic(MethodView):
    decorators = [allows.requires(IsAtleastModeratorInForum()), login_required]

    def post(self, topic_id, slug=None):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        topic.locked = False
        topic.save()
        return redirect(topic.url)


class HighlightTopic(MethodView):
    decorators = [allows.requires(IsAtleastModeratorInForum()), login_required]

    def post(self, topic_id, slug=None):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        topic.important = True
        topic.save()
        return redirect(topic.url)


class TrivializeTopic(MethodView):
    decorators = [allows.requires(IsAtleastModeratorInForum()), login_required]

    def post(self, topic_id=None, slug=None):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        topic.important = False
        topic.save()
        return redirect(topic.url)


class DeletePost(MethodView):
    decorators = [allows.requires(CanDeletePost), login_required]

    def post(self, post_id):
        post = Post.query.filter_by(id=post_id).first_or_404()
        first_post = post.first_post
        topic_url = post.topic.url
        forum_url = post.topic.forum.url

        post.delete()

        # If the post was the first post in the topic, redirect to the forums
        if first_post:
            return redirect(forum_url)
        return redirect(topic_url)


class RawPost(MethodView):
    decorators = [login_required]

    def get(self, post_id):
        post = Post.query.filter_by(id=post_id).first_or_404()
        return format_quote(username=post.username, content=post.content)


class MarkRead(MethodView):
    decorators = [login_required]

    def post(self, forum_id=None, slug=None):
        # Mark a single forum as read
        if forum_id is not None:
            forum_instance = Forum.query.filter_by(id=forum_id).first_or_404()
            forumsread = ForumsRead.query.filter_by(
                user_id=real(current_user).id, forum_id=forum_instance.id
            ).first()
            TopicsRead.query.filter_by(
                user_id=real(current_user).id, forum_id=forum_instance.id
            ).delete()

            if not forumsread:
                forumsread = ForumsRead()
                forumsread.user = real(current_user)
                forumsread.forum = forum_instance

            forumsread.last_read = time_utcnow()
            forumsread.cleared = time_utcnow()

            db.session.add(forumsread)
            db.session.commit()

            flash(_('Forum %(forum)s marked as read.', forum=forum_instance.title), 'success')

            return redirect(forum_instance.url)

        # Mark all forums as read
        ForumsRead.query.filter_by(user_id=real(current_user).id).delete()
        TopicsRead.query.filter_by(user_id=real(current_user).id).delete()

        forums = Forum.query.all()
        forumsread_list = []
        for forum_instance in forums:
            forumsread = ForumsRead()
            forumsread.user = real(current_user)
            forumsread.forum = forum_instance
            forumsread.last_read = time_utcnow()
            forumsread.cleared = time_utcnow()
            forumsread_list.append(forumsread)

        db.session.add_all(forumsread_list)
        db.session.commit()

        flash(_('All forums marked as read.'), 'success')

        return redirect(url_for('forum.index'))


class WhoIsOnline(MethodView):

    def get(self):
        if current_app.config['REDIS_ENABLED']:
            online_users = get_online_users()
        else:
            online_users = User.query.filter(User.lastseen >= time_diff()).all()
        return render_template('forum/online_users.html', online_users=online_users)


class TrackTopic(MethodView):
    decorators = [login_required]

    def post(self, topic_id, slug=None):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        real(current_user).track_topic(topic)
        real(current_user).save()
        return redirect(topic.url)


class UntrackTopic(MethodView):
    decorators = [login_required]

    def post(self, topic_id, slug=None):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        real(current_user).untrack_topic(topic)
        real(current_user).save()
        return redirect(topic.url)


class HideTopic(MethodView):
    decorators = [login_required]

    def post(self, topic_id, slug=None):
        topic = Topic.query.with_hidden().filter_by(id=topic_id).first_or_404()
        if not Permission(Has('makehidden'), IsAtleastModeratorInForum(forum=topic.forum)):
            flash(_("You do not have permission to hide this topic"), "danger")
            return redirect(topic.url)
        topic.hide(user=current_user)
        topic.save()

        if Permission(Has('viewhidden')):
            return redirect(topic.url)
        return redirect(topic.forum.url)


class UnhideTopic(MethodView):
    decorators = [login_required]

    def post(self, topic_id, slug=None):
        topic = Topic.query.filter_by(id=topic_id).first_or_404()
        if not Permission(Has('makehidden'), IsAtleastModeratorInForum(forum=topic.forum)):
            flash(_("You do not have permission to unhide this topic"), "danger")
            return redirect(topic.url)
        topic.unhide()
        topic.save()
        return redirect(topic.url)


class HidePost(MethodView):
    decorators = [login_required]

    def post(self, post_id):
        post = Post.query.filter(Post.id == post_id).first_or_404()

        if not Permission(Has('makehidden'), IsAtleastModeratorInForum(forum=post.topic.forum)):
            flash(_("You do not have permission to hide this post"), "danger")
            return redirect(post.topic.url)

        if post.hidden:
            flash(_("Post is already hidden"), "warning")
            return redirect(post.topic.url)

        first_post = post.first_post

        post.hide(current_user)
        post.save()

        if first_post:
            flash(_("Topic hidden"), "success")
        else:
            flash(_("Post hidden"), "success")

        if post.first_post and not Permission(Has("viewhidden")):
            return redirect(post.topic.forum.url)
        return redirect(post.topic.url)


class UnhidePost(MethodView):
    decorators = [login_required]

    def post(self, post_id):
        post = Post.query.filter(Post.id == post_id).first_or_404()

        if not Permission(Has('makehidden'), IsAtleastModeratorInForum(forum=post.topic.forum)):
            flash(_("You do not have permission to unhide this post"), "danger")
            return redirect(post.topic.url)

        if not post.hidden:
            flash(_("Post is already unhidden"), "warning")
            redirect(post.topic.url)

        post.unhide()
        post.save()
        flash(_("Post unhidden"), "success")
        return redirect(post.topic.url)


register_view(
    forum,
    routes=['/category/<int:category_id>', '/category/<int:category_id>-<slug>'],
    view_func=ViewCategory.as_view('view_category')
)
register_view(
    forum,
    routes=['/forum/<int:forum_id>/edit', '/forum/<int:forum_id>-<slug>/edit'],
    view_func=ManageForum.as_view('manage_forum')
)
register_view(
    forum,
    routes=['/forum/<int:forum_id>', '/forum/<int:forum_id>-<slug>'],
    view_func=ViewForum.as_view('view_forum')
)
register_view(
    forum,
    routes=['/<int:forum_id>/markread', '/<int:forum_id>-<slug>/markread'],
    view_func=MarkRead.as_view('markread')
)
register_view(
    forum,
    routes=['/<int:forum_id>/topic/new', '/<int:forum_id>-<slug>/topic/new'],
    view_func=NewTopic.as_view('new_topic')
)
register_view(forum, routes=['/memberlist'], view_func=MemberList.as_view('memberlist'))
register_view(
    forum, routes=['/post/<int:post_id>/delete'], view_func=DeletePost.as_view('delete_post')
)
register_view(forum, routes=['/post/<int:post_id>/edit'], view_func=EditPost.as_view('edit_post'))
register_view(forum, routes=['/post/<int:post_id>/raw'], view_func=RawPost.as_view('raw_post'))
register_view(
    forum, routes=['/post/<int:post_id>/report'], view_func=ReportView.as_view('report_post')
)
register_view(forum, routes=['/post/<int:post_id>'], view_func=ViewPost.as_view('view_post'))
register_view(forum, routes=['/search'], view_func=Search.as_view('search'))
register_view(
    forum,
    routes=['/topic/<int:topic_id>/delete', '/topic/<int:topic_id>-<slug>/delete'],
    view_func=DeleteTopic.as_view('delete_topic')
)
register_view(
    forum,
    routes=['/topic/<int:topic_id>/highlight', '/topic/<int:topic_id>-<slug>/highlight'],
    view_func=HighlightTopic.as_view('highlight_topic')
)
register_view(
    forum,
    routes=['/topic/<int:topic_id>/lock', '/topic/<int:topic_id>-<slug>/lock'],
    view_func=LockTopic.as_view('lock_topic')
)
register_view(
    forum,
    routes=['/topic/<int:topic_id>/post/<int:post_id>/reply'],
    view_func=ReplyPost.as_view('reply_post')
)
register_view(
    forum,
    routes=['/topic/<int:topic_id>/post/new', '/topic/<int:topic_id>-<slug>/post/new'],
    view_func=NewPost.as_view('new_post')
)
register_view(
    forum,
    routes=['/topic/<int:topic_id>', '/topic/<int:topic_id>-<slug>'],
    view_func=ViewTopic.as_view('view_topic')
)
register_view(
    forum,
    routes=['/topic/<int:topic_id>/trivialize', '/topic/<int:topic_id>-<slug>/trivialize'],
    view_func=TrivializeTopic.as_view('trivialize_topic')
)
register_view(
    forum,
    routes=['/topic/<int:topic_id>/unlock', '/topic/<int:topic_id>-<slug>/unlock'],
    view_func=UnlockTopic.as_view('unlock_topic')
)
register_view(
    forum,
    routes=['/topictracker/<int:topic_id>/add', '/topictracker/<int:topic_id>-<slug>/add'],
    view_func=TrackTopic.as_view('track_topic')
)
register_view(
    forum,
    routes=['/topictracker/<int:topic_id>/delete', '/topictracker/<int:topic_id>-<slug>/delete'],
    view_func=UntrackTopic.as_view('untrack_topic')
)
register_view(forum, routes=['/topictracker'], view_func=TopicTracker.as_view('topictracker'))
register_view(forum, routes=['/'], view_func=ForumIndex.as_view('index'))
register_view(forum, routes=['/who-is-online'], view_func=WhoIsOnline.as_view('who_is_online'))
register_view(
    forum,
    routes=["/topic/<int:topic_id>/hide", "/topic/<int:topic_id>-<slug>/hide"],
    view_func=HideTopic.as_view('hide_topic')
)
register_view(
    forum,
    routes=["/topic/<int:topic_id>/unhide", "/topic/<int:topic_id>-<slug>/unhide"],
    view_func=UnhideTopic.as_view('unhide_topic')
)
register_view(forum, routes=["/post/<int:post_id>/hide"], view_func=HidePost.as_view('hide_post'))
register_view(
    forum, routes=["/post/<int:post_id>/unhide"], view_func=UnhidePost.as_view('unhide_post')
)
