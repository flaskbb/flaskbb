# -*- coding: utf-8 -*-
"""
flaskbb.forum.locals
~~~~~~~~~~~~~~~~~~~~
Thread local helpers for FlaskBB

:copyright: 2017, the FlaskBB Team
:license: BSD, see license for more details
"""

from typing import Any

from flask import g, request
from sqlalchemy import select
from werkzeug.local import LocalProxy

from flaskbb.extensions import db

from .models import Category, Forum, Post, Topic


@LocalProxy
def current_post() -> Post | None:
    return _get_item(Post, "post_id", "post")


@LocalProxy
def current_topic() -> Topic | None:
    if current_post:
        return current_post.topic
    return _get_item(Topic, "topic_id", "topic")


@LocalProxy
def current_forum() -> Forum | None:
    if current_topic:
        return current_topic.forum
    return _get_item(Forum, "forum_id", "forum")


@LocalProxy
def current_category() -> Category | None:
    if current_forum:
        return current_forum.category
    return _get_item(Category, "category_id", "category")


def _get_item(model: Any, view_arg: str, name: str):
    if (
        g
        and not getattr(g, name, None)
        and request.view_args
        and view_arg in request.view_args
    ):
        result = db.session.execute(
            select(model).filter_by(id=request.view_args[view_arg])
        ).scalar()
        setattr(g, name, result)
    return getattr(g, name, None)
