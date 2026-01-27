from __future__ import annotations

import typing as t

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm
from flask_sqlalchemy.pagination import Pagination
from flaskbb.extensions import db

class SelectAllPagination(Pagination):
    """Returned by :meth:`.SQLAlchemy.paginate`. Takes ``select`` and ``session``
    arguments in addition to the :class:`Pagination` arguments.

    .. versionadded:: 3.0
    """

    def _query_items(self) -> list[t.Any]:
        select = self._query_args["select"]
        select = select.limit(self.per_page).offset(self._query_offset)
        session = self._query_args["session"]
        return session.execute(select).all()

    def _query_count(self) -> int:
        select = self._query_args["select"]
        sub = select.options(sa_orm.lazyload("*")).order_by(None).subquery()
        session = self._query_args["session"]
        out = session.execute(sa.select(sa.func.count()).select_from(sub)).scalar()
        return out  # type: ignore[no-any-return]


def paginate(
    select: sa.sql.Select[t.Any],
    *,
    page: int | None = None,
    per_page: int | None = None,
    max_per_page: int | None = None,
    error_out: bool = True,
    count: bool = True,
) -> Pagination:
    """Apply an offset and limit to a select statment based on the current page and
    number of items per page, returning a :class:`.Pagination` object.

    The statement should select a model class, like ``select(User)``. This applies
    ``unique()`` and ``scalars()`` modifiers to the result, so compound selects will
    not return the expected results.

    :param select: The ``select`` statement to paginate.
    :param page: The current page, used to calculate the offset. Defaults to the
        ``page`` query arg during a request, or 1 otherwise.
    :param per_page: The maximum number of items on a page, used to calculate the
        offset and limit. Defaults to the ``per_page`` query arg during a request,
        or 20 otherwise.
    :param max_per_page: The maximum allowed value for ``per_page``, to limit a
        user-provided value. Use ``None`` for no limit. Defaults to 100.
    :param error_out: Abort with a ``404 Not Found`` error if no items are returned
        and ``page`` is not 1, or if ``page`` or ``per_page`` is less than 1, or if
        either are not ints.
    :param count: Calculate the total number of values by issuing an extra count
        query. For very complex queries this may be inaccurate or slow, so it can be
        disabled and set manually if necessary.

    .. versionchanged:: 3.0
        The ``count`` query is more efficient.

    .. versionadded:: 3.0
    """
    return SelectAllPagination(
        select=select,
        session=db.session,
        page=page,
        per_page=per_page,
        max_per_page=max_per_page,
        error_out=error_out,
        count=count,
    )
