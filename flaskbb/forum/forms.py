# -*- coding: utf-8 -*-
"""
    flaskbb.forum.forms
    ~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the forum views.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask.ext.wtf import Form, Required, TextAreaField, TextField

from flaskbb.forum.models import Topic, Post

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
