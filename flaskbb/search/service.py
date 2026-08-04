"""
flaskbb.search.service
~~~~~~~~~~~~~~~~~~~~~~~

Query composition for the global search: runs the pluggable
`flaskbb_search` backend and layers permission scoping and filters on
top of the returned `Select` statements.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from datetime import date, datetime, time, timedelta, UTC
from typing import Any

from markupsafe import Markup
from sqlalchemy import Select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.elements import ColumnElement

from flaskbb.extensions import flaskbb_search
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.user.models import User
from flaskbb.utils.queries import hidden


def search_forums(
    query: str,
    user: "User",
    *,
    content_type: str = "topic",
    forum: Forum | None = None,
    author: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    state: str = "",
) -> dict[str, Select[Any]]:
    """Search either topics or posts (never both, never forums by name),
    scoped to forums `user` can access.

    :param query: The search term.
    :param user: The user performing the search - determines which
                 forums are visible and whether hidden content can be
                 requested via `state="hidden"`.
    :param content_type: Either "topic" or "post" - which model to
                          search. Defaults to "topic".
    :param forum: Restrict results to a single forum (still subject to
                  the accessibility check above).
    :param author: Filter by username (substring match).
    :param date_from: Only include topics/posts created on or after
                       this date.
    :param date_to: Only include topics/posts created on or before
                     this date.
    :param state: One of "" (any), "locked", "unlocked", "important",
                  "hidden". "hidden" is silently ignored unless `user`
                  has the `viewhidden` permission. "locked"/"unlocked"/
                  "important" filter on the (containing, for posts)
                  topic's state.
    """
    model = Post if content_type == "post" else Topic
    accessible_ids = [f.id for f in Forum.get_accessible(user)]

    def topic_clause(clause: ColumnElement[bool]) -> ColumnElement[bool]:
        return clause if model is Topic else Post.topic.has(clause)

    stmt = flaskbb_search.search(model, query).where(
        topic_clause(Topic.forum_id.in_(accessible_ids))
    )

    if forum is not None:
        stmt = stmt.where(topic_clause(Topic.forum_id == forum.id))

    if author:
        stmt = stmt.where(model.username.ilike(f"%{author}%"))

    # `date_created` is a tz-aware UTC datetime column (UTCDateTime), but the
    # form's DateField yields a plain `date` - bind UTC day boundaries so the
    # comparison has tzinfo and `date_to` includes the whole selected day.
    if date_from:
        start = datetime.combine(date_from, time.min, tzinfo=UTC)
        stmt = stmt.where(model.date_created >= start)

    if date_to:
        end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
        stmt = stmt.where(model.date_created < end)

    if state == "locked":
        stmt = stmt.where(topic_clause(Topic.locked.is_(True)))
    elif state == "unlocked":
        stmt = stmt.where(topic_clause(Topic.locked.is_(False)))
    elif state == "important":
        stmt = stmt.where(topic_clause(Topic.important.is_(True)))

    # `hidden()`'s own default (`hidden=None`) branch checks Flask-Login's
    # global `current_user`, which may not be `user` (e.g. in tests, or
    # any future caller searching on someone else's behalf) - always pass
    # an explicit True/False here so scoping only ever depends on `user`.
    has_viewhidden = bool(user.is_authenticated and user.permissions.get("viewhidden"))
    if state == "hidden" and has_viewhidden:
        stmt = hidden(stmt, hidden=True)
    elif not has_viewhidden:
        stmt = hidden(stmt, hidden=False)

    if model is Topic:
        stmt = stmt.options(joinedload(Topic.forum), joinedload(Topic.first_post))
    else:
        stmt = stmt.options(joinedload(Post.topic).joinedload(Topic.forum))

    return {content_type: stmt}


def search_users(query: str) -> dict[str, Select[Any]]:
    return {"user": flaskbb_search.search(User, query)}


def search_snippet(instance: Topic | Post, query: str) -> Markup:
    """Returns a highlighted content preview of `instance` (a `Topic` or
    `Post` search result) for `query`, via the active search backend.
    """
    content = instance.first_post.content if isinstance(instance, Topic) else instance.content
    return flaskbb_search.snippet(type(instance), instance.id, content, query)
