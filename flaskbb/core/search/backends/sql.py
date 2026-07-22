# -*- coding: utf-8 -*-
"""
flaskbb.core.search.backends.sql
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A dependency-free search backend that searches directly against the
database via ILIKE. The row is the index, so index/update/remove/
reindex are all no-ops. This is FlaskBB's default backend.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from collections.abc import Callable, Sequence
from typing import Any, override

from flask_sqlalchemy.model import Model
from sqlalchemy import Select, or_, select
from sqlalchemy.sql.elements import ColumnElement

from flaskbb.core.search.base import ModelT, SearchBackend
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.user.models import User


def _escape_like(term: str) -> str:
    """Escape LIKE metacharacters in a user-supplied search term so
    literal `%`/`_` in the input aren't interpreted as SQL wildcards.
    """
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _post_clause(term: str) -> ColumnElement[bool]:
    return or_(
        Post.username.ilike(term, escape="\\"),
        Post.modified_by.ilike(term, escape="\\"),
        Post.content.ilike(term, escape="\\"),
    )


def _topic_clause(term: str) -> ColumnElement[bool]:
    return or_(
        Topic.title.ilike(term, escape="\\"),
        Topic.username.ilike(term, escape="\\"),
        Topic.first_post.has(Post.content.ilike(term, escape="\\")),
    )


def _forum_clause(term: str) -> ColumnElement[bool]:
    return or_(
        Forum.title.ilike(term, escape="\\"),
        Forum.description.ilike(term, escape="\\"),
    )


def _user_clause(term: str) -> ColumnElement[bool]:
    return or_(
        User.username.ilike(term, escape="\\"),
        User.email.ilike(term, escape="\\"),
    )


class SQLSearchBackend(SearchBackend):
    """Searches directly against SQL columns via ILIKE. No external
    index, no dependency beyond SQLAlchemy - suitable as the default
    and for running in the test suite.
    """

    _FILTERS: dict[ModelT, Callable[[str], ColumnElement[bool]]] = {
        Post: _post_clause,
        Topic: _topic_clause,
        Forum: _forum_clause,
        User: _user_clause,
    }

    @override
    def index(self, instance: Model) -> None:
        pass

    @override
    def update(self, instance: Model) -> None:
        pass

    @override
    def remove(self, instance: Model) -> None:
        pass

    @override
    def reindex(self, models: Sequence[ModelT] | None = None) -> None:
        pass

    @override
    def search(self, model: ModelT, query: str) -> Select[Any]:
        filter_fn = self._FILTERS.get(model)
        if filter_fn is None:
            raise ValueError(f"{model.__name__} is not a searchable model")
        term = f"%{_escape_like(query)}%"
        return select(model).where(filter_fn(term))
