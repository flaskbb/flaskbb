"""
flaskbb.utils.database
~~~~~~~~~~~~~~~~~~~~~~

Some database helpers such as a CRUD mixin.

:copyright: (c) 2015 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import datetime
import logging
import typing as t

import sqlalchemy as sa
import sqlalchemy.types as types
from flask import abort
from flask_sqlalchemy.session import Session
from sqlalchemy.orm import (
    declarative_mixin,
    declared_attr,
    InstrumentedAttribute,
    Mapped,
    mapped_column,
    relationship,
    scoped_session,
)

from flaskbb.extensions import db

if t.TYPE_CHECKING:
    from flaskbb.user.models import User

from ..core.exceptions import PersistenceError

logger = logging.getLogger(__name__)


def make_comparable(cls):
    def __eq__(self, other):
        return isinstance(other, cls) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((cls, self.id))

    cls.__eq__ = __eq__
    cls.__ne__ = __ne__
    cls.__hash__ = __hash__
    return cls


class CRUDMixin:
    if t.TYPE_CHECKING:
        # every model mixing this in declares its own primary key and is
        # mapped by the declarative metaclass, which supplies __table__ and
        # the kwargs-only declarative constructor
        id: Mapped[int] = mapped_column(primary_key=True)
        __table__: t.ClassVar[sa.Table]

        def __init__(self, **kwargs: t.Any) -> None: ...

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    @classmethod
    def get(cls, *clause: sa.ColumnExpressionArgument[bool]):
        result = db.session.execute(sa.select(cls).where(*clause)).scalar()
        return result

    @classmethod
    def get_or_404(cls, *clause: sa.ColumnExpressionArgument[bool]):
        result = cls.get(*clause)
        if not result:
            abort(404)
        return result

    @classmethod
    def get_by(cls, **kwargs: t.Any):
        return db.session.execute(sa.select(cls).filter_by(**kwargs)).scalar()

    @classmethod
    def get_by_or_404(cls, **kwargs: t.Any):
        result = cls.get_by(**kwargs)
        if not result:
            abort(404)
        return result

    @classmethod
    def get_all(cls, *clause: sa.ColumnExpressionArgument[bool]) -> list[t.Self]:
        return list(db.session.execute(sa.select(cls).where(*clause)).scalars())

    @classmethod
    def count(
        cls,
        clause: list[sa.ColumnExpressionArgument[bool]]
        | sa.ColumnExpressionArgument[bool]
        | None = None,
        column: InstrumentedAttribute[t.Any] | None = None,
    ) -> int:
        if column is None:
            column = cls.id

        stmt = db.select(db.func.count(column))
        if clause is not None:
            if not isinstance(clause, list):
                clause = [clause]
            stmt = stmt.where(*clause)
        return db.session.execute(stmt).scalar_one()

    @classmethod
    def create(cls, **kwargs: t.Any):
        instance = cls(**kwargs)
        return instance.save()

    def save(self) -> t.Self | None:
        """Saves the object to the database."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self) -> t.Self | None:
        """Delete the object from the database."""
        db.session.delete(self)
        db.session.commit()
        return self


class UTCDateTime(types.TypeDecorator[datetime.datetime]):
    impl = types.DateTime
    cache_ok = True

    @t.override
    def process_bind_param(
        self, value: datetime.datetime | None, dialect: sa.Dialect
    ) -> datetime.datetime | None:
        """Way into the database."""
        if value is not None:
            if not value.tzinfo or value.tzinfo.utcoffset(value) is None:
                raise TypeError("tzinfo is required")
            value = value.astimezone(datetime.UTC).replace(tzinfo=None)
        return value

    @t.override
    def process_result_value(
        self, value: t.Any | None, dialect: sa.Dialect
    ) -> datetime.datetime | None:
        """Way out of the database."""
        if value is not None:
            value = value.replace(tzinfo=datetime.UTC)
        return value


@declarative_mixin
class HideableMixin:
    hidden: Mapped[bool] = mapped_column(default=False, nullable=False)
    hidden_at: Mapped[datetime.datetime | None] = mapped_column(
        UTCDateTime(timezone=True), nullable=True
    )

    @declared_attr
    def hidden_by_id(cls) -> Mapped[int | None]:
        return mapped_column(
            sa.ForeignKey("users.id", name=f"fk_{cls.__name__}_hidden_by"),  # pyright: ignore
            nullable=True,
        )

    @declared_attr
    def hidden_by(cls) -> Mapped["User"]:
        return relationship("User", uselist=False, foreign_keys=[cls.hidden_by_id])  # pyright: ignore

    def hide(self, user: "User", *args: t.Any, **kwargs: t.Any) -> t.Self | None:
        from flaskbb.utils.helpers import time_utcnow

        self.hidden_by = user
        self.hidden = True
        self.hidden_at = time_utcnow()
        return self

    def unhide(self, *args: t.Any, **kwargs: t.Any) -> t.Self | None:
        self.hidden_by = None
        self.hidden = False
        self.hidden_at = None
        return self


class HideableCRUDMixin(HideableMixin, CRUDMixin):
    pass


def try_commit(session: Session | scoped_session[Session], message: str = "Error while saving"):
    try:
        session.commit()
    except Exception as e:
        raise PersistenceError(message) from e


def drop_all():
    """Drops every table.

    SQLite cannot DROP tables whose foreign keys are mutually dependent.
    `defer_foreign_keys`` is needed since ``foreign_keys`` is a no-op while a transaction is open.
    """
    if db.engine.dialect.name != "sqlite":
        db.drop_all()
        return

    with db.engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("PRAGMA defer_foreign_keys=ON")
        db.metadata.drop_all(bind=connection)
        connection.commit()

        # the connection goes back to the pool afterwards, where the connect
        # listener that normally turns this on will not run again
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.commit()
