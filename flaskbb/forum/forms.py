# -*- coding: utf-8 -*-
"""
    flaskbb.forum.forms
    ~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the forum views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask_wtf import FlaskForm
from wtforms import (TextAreaField, StringField, SelectMultipleField,
                     BooleanField, SubmitField)
from wtforms.validators import DataRequired, Optional, Length
from flask_babelplus import lazy_gettext as _

from flaskbb.forum.models import Topic, Post, Report, Forum
from flaskbb.user.models import User


class QuickreplyForm(FlaskForm):
    content = TextAreaField(_("Quick reply"), validators=[
        DataRequired(message=_("You cannot post a reply without content."))])

    submit = SubmitField(_("Reply"))

    def save(self, user, topic):
        post = Post(content=self.content.data)
        return post.save(user=user, topic=topic)


class ReplyForm(FlaskForm):
    content = TextAreaField(_("Content"), validators=[
        DataRequired(message=_("You cannot post a reply without content."))])

    track_topic = BooleanField(_("Track this topic"), default=False,
                               validators=[Optional()])

    submit = SubmitField(_("Reply"))
    preview = SubmitField(_("Preview"))

    def save(self, user, topic):
        post = Post(content=self.content.data)

        if self.track_topic.data:
            user.track_topic(topic)
        return post.save(user=user, topic=topic)


class NewTopicForm(ReplyForm):
    title = StringField(_("Topic title"), validators=[
        DataRequired(message=_("Please choose a title for your topic."))])

    content = TextAreaField(_("Content"), validators=[
        DataRequired(message=_("You cannot post a reply without content."))])

    track_topic = BooleanField(_("Track this topic"), default=False,
                               validators=[Optional()])

    submit = SubmitField(_("Post Topic"))
    preview = SubmitField(_("Preview"))

    def save(self, user, forum):
        topic = Topic(title=self.title.data)
        post = Post(content=self.content.data)

        if self.track_topic.data:
            user.track_topic(topic)
        return topic.save(user=user, forum=forum, post=post)


class ReportForm(FlaskForm):
    reason = TextAreaField(_("Reason"), validators=[
        DataRequired(message=_("What is the reason for reporting this post?"))
    ])

    submit = SubmitField(_("Report post"))

    def save(self, user, post):
        report = Report(reason=self.reason.data)
        return report.save(post=post, user=user)


class UserSearchForm(FlaskForm):
    search_query = StringField(_("Search"), validators=[
        DataRequired(), Length(min=3, max=50)
    ])

    submit = SubmitField(_("Search"))

    def get_results(self):
        query = self.search_query.data
        return User.query.whooshee_search(query)


class SearchPageForm(FlaskForm):
    search_query = StringField(_("Criteria"), validators=[
        DataRequired(), Length(min=3, max=50)])

    search_types = SelectMultipleField(_("Content"), validators=[
        DataRequired()], choices=[('post', _('Post')), ('topic', _('Topic')),
                                  ('forum', _('Forum')), ('user', _('Users'))])

    submit = SubmitField(_("Search"))

    def get_results(self):
        # Because the DB is not yet initialized when this form is loaded,
        # the query objects cannot be instantiated in the class itself
        search_actions = {
            'post': Post.query.whooshee_search,
            'topic': Topic.query.whooshee_search,
            'forum': Forum.query.whooshee_search,
            'user': User.query.whooshee_search
        }

        query = self.search_query.data
        types = self.search_types.data
        results = {}

        for search_type in search_actions.keys():
            if search_type in types:
                results[search_type] = search_actions[search_type](query)

        return results
