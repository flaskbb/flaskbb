# -*- coding: utf-8 -*-
"""
    flaskbb.utils.search
    ~~~~~~~~~~~~~~~~~~~~

    This module contains all the whoosheers for FlaskBB's
    full text search.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
import whoosh
from flask_whooshee import AbstractWhoosheer

from flaskbb._compat import text_type
from flaskbb.forum.models import Forum, Topic, Post
from flaskbb.user.models import User


logger = logging.getLogger(__name__)


class PostWhoosheer(AbstractWhoosheer):
    models = [Post]

    schema = whoosh.fields.Schema(
        post_id=whoosh.fields.NUMERIC(stored=True, unique=True),
        username=whoosh.fields.TEXT(),
        modified_by=whoosh.fields.TEXT(),
        content=whoosh.fields.TEXT()
    )

    @classmethod
    def update_post(cls, writer, post):
        writer.update_document(
            post_id=post.id,
            username=text_type(post.username),
            modified_by=text_type(post.modified_by),
            content=text_type(post.content)
        )

    @classmethod
    def insert_post(cls, writer, post):
        writer.add_document(
            post_id=post.id,
            username=text_type(post.username),
            modified_by=text_type(post.modified_by),
            content=text_type(post.content)
        )

    @classmethod
    def delete_post(cls, writer, post):
        writer.delete_by_term('post_id', post.id)


class TopicWhoosheer(AbstractWhoosheer):
    models = [Topic]

    schema = whoosh.fields.Schema(
        topic_id=whoosh.fields.NUMERIC(stored=True, unique=True),
        title=whoosh.fields.TEXT(),
        username=whoosh.fields.TEXT(),
        content=whoosh.fields.TEXT()
    )

    @classmethod
    def update_topic(cls, writer, topic):
        writer.update_document(
            topic_id=topic.id,
            title=text_type(topic.title),
            username=text_type(topic.username),
            content=text_type(getattr(topic.first_post, 'content', None))
        )

    @classmethod
    def insert_topic(cls, writer, topic):
        writer.add_document(
            topic_id=topic.id,
            title=text_type(topic.title),
            username=text_type(topic.username),
            content=text_type(getattr(topic.first_post, 'content', None))
        )

    @classmethod
    def delete_topic(cls, writer, topic):
        writer.delete_by_term('topic_id', topic.id)


class ForumWhoosheer(AbstractWhoosheer):
    models = [Forum]

    schema = whoosh.fields.Schema(
        forum_id=whoosh.fields.NUMERIC(stored=True, unique=True),
        title=whoosh.fields.TEXT(),
        description=whoosh.fields.TEXT()
    )

    @classmethod
    def update_forum(cls, writer, forum):
        writer.update_document(
            forum_id=forum.id,
            title=text_type(forum.title),
            description=text_type(forum.description)
        )

    @classmethod
    def insert_forum(cls, writer, forum):
        writer.add_document(
            forum_id=forum.id,
            title=text_type(forum.title),
            description=text_type(forum.description)
        )

    @classmethod
    def delete_forum(cls, writer, forum):
        writer.delete_by_term('forum_id', forum.id)


class UserWhoosheer(AbstractWhoosheer):
    models = [User]

    schema = whoosh.fields.Schema(
        user_id=whoosh.fields.NUMERIC(stored=True, unique=True),
        username=whoosh.fields.TEXT(),
        email=whoosh.fields.TEXT()
    )

    @classmethod
    def update_user(cls, writer, user):
        writer.update_document(
            user_id=user.id,
            username=text_type(user.username),
            email=text_type(user.email)
        )

    @classmethod
    def insert_user(cls, writer, user):
        writer.add_document(
            user_id=user.id,
            username=text_type(user.username),
            email=text_type(user.email)
        )

    @classmethod
    def delete_user(cls, writer, user):
        writer.delete_by_term('user_id', user.id)
