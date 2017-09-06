# -*- coding: utf-8 -*-
"""
    flaskbb.forum.locals
    ~~~~~~~~~~~~~~~~~~~~
    Thread local helpers for FlaskBB

    :copyright: 2017, the FlaskBB Team
    :license: BSD, see license for more details
"""

from flask import _request_ctx_stack, has_request_context, request
from werkzeug.local import LocalProxy

from .models import Category, Forum, Post, Topic


@LocalProxy
def current_post():
    return _get_item(Post, 'post_id', 'post')


@LocalProxy
def current_topic():
    if current_post:
        return current_post.topic
    return _get_item(Topic, 'topic_id', 'topic')


@LocalProxy
def current_forum():
    if current_topic:
        return current_topic.forum
    return _get_item(Forum, 'forum_id', 'forum')


@LocalProxy
def current_category():
    if current_forum:
        return current_forum.category
    return _get_item(Category, 'category_id', 'category')


def _get_item(model, view_arg, name):
    if (
        has_request_context() and
        not getattr(_request_ctx_stack.top, name, None) and
        view_arg in request.view_args
    ):
        setattr(
            _request_ctx_stack.top,
            name,
            model.query.filter_by(id=request.view_args[view_arg]).first()
        )

    return getattr(_request_ctx_stack.top, name, None)
