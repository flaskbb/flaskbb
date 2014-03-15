# -*- coding: utf-8 -*-
"""
    flaskbb.forum.forms
    ~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the forum views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask.ext.wtf import Form
from wtforms import TextAreaField, TextField, SelectMultipleField
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


class UserSearchForm(Form):
    search_query = TextField("Search", validators=[Optional(), Length(min=3, max=50)])

    def get_results(self):
        query = self.search_query.data
        return User.query.whoosh_search(query)


class SearchPageForm(Form):
    search_query = TextField("Criteria", validators=[Required(), Length(min=3, max=50)])
    search_types = SelectMultipleField("Content", validators=[Required()], choices=[
        ('post', 'Post'), ('topic', 'Topic'), ('forum', 'Forum'), ('user', 'Users')])

    def get_results(self):
        # Because the DB is not yet initialized when this form is loaded, the query objects cannot be instantiated
        # in the class itself
        search_actions = {
            'post': Post.query.whoosh_search,
            'topic': Topic.query.whoosh_search,
            'forum': Forum.query.whoosh_search,
            'user': User.query.whoosh_search
        }

        query = self.search_query.data
        types = self.search_types.data
        results = {}

        for type in search_actions.keys():
            if type in types:
                results[type] = search_actions[type](query)

        return results