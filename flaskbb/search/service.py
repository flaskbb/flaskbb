# -*- coding: utf-8 -*-
"""
flaskbb.search.service
~~~~~~~~~~~~~~~~~~~~~~~

Query composition for the global search: runs the pluggable
`flaskbb_search` backend and layers permission scoping and filters on
top of the returned `Select` statements.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from datetime import date
from typing import Any

from sqlalchemy import Select

from flaskbb.extensions import flaskbb_search
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.user.models import User
from flaskbb.utils.queries import hidden


def search_forums(
    query: str,
    user: "User",
    *,
    forum: Forum | None = None,
    author: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    state: str = "",
) -> dict[str, Select[Any]]:
    """Search topics and posts, scoped to forums `user` can access.

    :param query: The search term.
    :param user: The user performing the search - determines which
                 forums are visible and whether hidden content can be
                 requested via `state="hidden"`.
    :param forum: Restrict results to a single forum (still subject to
                  the accessibility check above).
    :param author: Filter by username (substring match).
    :param date_from: Only include topics/posts created on or after
                       this date.
    :param date_to: Only include topics/posts created on or before
                     this date.
    :param state: One of "" (any), "locked", "unlocked", "important",
                  "hidden". "hidden" is silently ignored unless `user`
                  has the `viewhidden` permission.
    """
    accessible_ids = [f.id for f in Forum.get_accessible(user)]

    topic_stmt = flaskbb_search.search(Topic, query).where(
        Topic.forum_id.in_(accessible_ids)
    )
    post_stmt = flaskbb_search.search(Post, query).where(
        Post.topic.has(Topic.forum_id.in_(accessible_ids))
    )

    if forum is not None:
        topic_stmt = topic_stmt.where(Topic.forum_id == forum.id)
        post_stmt = post_stmt.where(Post.topic.has(Topic.forum_id == forum.id))

    if author:
        term = f"%{author}%"
        topic_stmt = topic_stmt.where(Topic.username.ilike(term))
        post_stmt = post_stmt.where(Post.username.ilike(term))

    if date_from:
        topic_stmt = topic_stmt.where(Topic.date_created >= date_from)
        post_stmt = post_stmt.where(Post.date_created >= date_from)

    if date_to:
        topic_stmt = topic_stmt.where(Topic.date_created <= date_to)
        post_stmt = post_stmt.where(Post.date_created <= date_to)

    if state == "locked":
        topic_stmt = topic_stmt.where(Topic.locked.is_(True))
    elif state == "unlocked":
        topic_stmt = topic_stmt.where(Topic.locked.is_(False))
    elif state == "important":
        topic_stmt = topic_stmt.where(Topic.important.is_(True))

    has_viewhidden = bool(user.is_authenticated and user.permissions.get("viewhidden"))
    if state == "hidden" and has_viewhidden:
        topic_stmt = hidden(topic_stmt, hidden=True)
        post_stmt = hidden(post_stmt, hidden=True)
    elif not has_viewhidden:
        topic_stmt = hidden(topic_stmt, hidden=False)
        post_stmt = hidden(post_stmt, hidden=False)

    return {"topic": topic_stmt, "post": post_stmt}


def search_users(query: str) -> dict[str, Select[Any]]:
    return {"user": flaskbb_search.search(User, query)}
