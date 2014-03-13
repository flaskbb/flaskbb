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
from wtforms.validators import Required, Optional, Length

from flaskbb.forum.models import Topic, Post, Report, Forum, Category
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

    def __init__(self, search_types=list()):
        super(SearchForm, self).__init__()
        self.search_types = search_types

    search_query = TextField("Search", validators=[Optional(), Length(min=3, max=50)])

    def get_types(self):
        return self.search_types

    def get_results(self):
        results = {}
        types = self.get_types()
        query = self.search_query.data
        for type in types:
            if type == 'user':
                results['user'] = User.query.whoosh_search(query)
            elif type == 'post':
                results['post'] = Post.query.whoosh_search(query)
            elif type == 'topic':
                results['topic'] = Topic.query.whoosh_search(query)
            elif type == 'forum':
                results['forum'] = Forum.query.whoosh_search(query)
            elif type == 'category':
                results['category'] = Category.query.whoosh_search(query)
        return results