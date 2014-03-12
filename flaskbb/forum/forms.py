# -*- coding: utf-8 -*-
"""
    flaskbb.forum.forms
    ~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the forum views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask.ext.wtf import Form
import flask.ext.whooshalchemy
from wtforms import TextAreaField, TextField, BooleanField, FormField, SelectMultipleField
from wtforms.validators import Required

from flaskbb.forum.models import Topic, Post, Report
from flaskbb.user.models import User


class QuickreplyForm(Form):
    content = TextAreaField("Quickreply", validators=[
        Required(message="You cannot post a reply without content.")])

    def save(self, user, topic):
        post = Post(**self.data)
        return post.save(user=user, topic=topic)


class ReplyForm(Form):
    content = TextAreaField("Content", validators=[
        Required(message="You cannot post a reply without content.")])

    def save(self, user, topic):
        post = Post(**self.data)
        return post.save(user=user, topic=topic)


class NewTopicForm(ReplyForm):
    title = TextField("Topic Title", validators=[
        Required(message="A topic title is required")])
    content = TextAreaField("Content", validators=[
        Required(message="You cannot post a reply without content.")])

    def save(self, user, forum):
        topic = Topic(title=self.title.data)
        post = Post(content=self.content.data)
        return topic.save(user=user, forum=forum, post=post)


class ReportForm(Form):
    reason = TextAreaField("Reason", validators=[
        Required(message="Please insert a reason why you want to report this \
                          post")
    ])

    def save(self, user, post):
        report = Report(**self.data)
        return report.save(user, post)


class SearchForm(Form):
    search_types = SelectMultipleField("Search Types", validators=[
        Required("Please insert at least one search type")], choices=[
        ('user', 'User'), ('post', 'Post'), ('topic', 'Topic'), ('forum', 'Forum'), ('category', 'Category')
    ])
    search_query = TextField("Search Query", validators=[
        Required(message="Please insert a search query")
    ])

    def fetch_types(self):
        return self.search_types.data

    def fetch_results(self):
        results = {}
        types = self.fetch_types()
        for type in types:
            if type == 'user':
                results['user'] = User.query.whoosh_search(self.search_query)
        print(results)