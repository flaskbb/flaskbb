# -*- coding: utf-8 -*-
"""
flaskbb.core.search.spec
~~~~~~~~~~~~~~~~~~~~~~~~~~

The searchable-field mapping shared by the database-native search
backends (`postgresql`, `sqlite`): which columns of which table each
backend indexes. Nullable columns are coalesced to '' when indexed.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from flaskbb.core.search.base import ModelT
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.user.models import User

# (model, table, indexed columns)
INDEX_SPECS: tuple[tuple[ModelT, str, tuple[str, ...]], ...] = (
    (Post, "posts", ("username", "modified_by", "content")),
    (Topic, "topics", ("title", "username")),
    (Forum, "forums", ("title", "description")),
    (User, "users", ("username", "email")),
)

# model -> table name
TABLES: dict[ModelT, str] = {model: table for model, table, _cols in INDEX_SPECS}
