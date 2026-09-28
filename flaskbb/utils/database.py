"""
flaskbb.utils.database
~~~~~~~~~~~~~~~~~~~~~~

Some database helpers such as a CRUD mixin.

create_database and database_exists are taken
from sqlalchemy-utils and its LICENSE (BSD-3-Clause) applies.

:copyright: (c) 2015 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import datetime
import logging
import os
import typing as t

import sqlalchemy as sa
import sqlalchemy.types as types
from flask import abort
from flask_sqlalchemy.session import Session
from sqlalchemy.exc import OperationalError, ProgrammingError
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


class HasId(t.Protocol):
    # ``Any`` rather than ``Mapped[int]``: the two type checkers disagree on
    # what a mapped attribute looks like to a protocol (basedpyright sees
    # ``Mapped[int]``, mypy sees ``int``), and only its existence matters here
    id: t.Any


def make_comparable[T: HasId](cls: type[T]) -> type[T]:
    def __eq__(self: T, other: object) -> bool:
        return isinstance(other, cls) and self.id == other.id

    def __ne__(self: T, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self: T) -> int:
        return hash((cls, self.id))

    # the slots are typed with an ``object`` self, so a narrower one never fits
    cls.__eq__ = __eq__  # type: ignore[method-assign,assignment]
    cls.__ne__ = __ne__  # type: ignore[method-assign,assignment]
    cls.__hash__ = __hash__  # type: ignore[method-assign,assignment]
    return cls


if t.TYPE_CHECKING:
    from flask_sqlalchemy.model import Model as _FSAModel
    from sqlalchemy.orm import DeclarativeBase

    class _DeclarativeBase(_FSAModel, DeclarativeBase):
        pass

else:
    _DeclarativeBase = db.Model


class BaseModel(_DeclarativeBase):
    """Declarative base for every FlaskBB model, with the CRUD helpers."""

    __abstract__ = True

    if t.TYPE_CHECKING:
        # mapped by the declarative metaclass, which supplies __table__
        __table__: t.ClassVar[sa.FromClause]

    @t.override
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
        # counting rows instead of a primary key column keeps this working
        # for models with a composite primary key and no ``id``
        count = sa.func.count() if column is None else sa.func.count(column)
        stmt = sa.select(count).select_from(cls)
        if clause is not None:
            if not isinstance(clause, list):
                clause = [clause]
            stmt = stmt.where(*clause)
        return db.session.execute(stmt).scalar_one()

    @classmethod
    def create(cls, **kwargs: t.Any):
        instance = cls(**kwargs)
        return instance.save()

    def save(self) -> t.Self:
        """Saves the object to the database."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self) -> t.Self:
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
    @classmethod
    def hidden_by_id(cls) -> Mapped[int | None]:
        return mapped_column(
            sa.ForeignKey("users.id", name=f"fk_{cls.__name__}_hidden_by"),
            nullable=True,
        )

    @declared_attr
    @classmethod
    def hidden_by(cls) -> Mapped["User"]:
        return relationship("User", uselist=False, foreign_keys=[cls.hidden_by_id])

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


def _url_with_database(url: sa.engine.url.URL, database: str | None) -> sa.engine.url.URL:
    # URL.set() cannot unset the database, so rebuild the URL instead
    return sa.engine.url.URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database=database,
        query=url.query,
    )


def _sqlite_file_exists(database: str) -> bool:
    if not os.path.isfile(database) or os.path.getsize(database) < 100:
        return False

    with open(database, "rb") as fp:
        return fp.read(16) == b"SQLite format 3\x00"


def database_exists(url: sa.engine.url.URL) -> bool:
    """Checks if the database behind ``url`` exists."""
    dialect = url.get_dialect().name

    if dialect == "sqlite":
        # a URL without a database is an anonymous in-memory database
        if not url.database or url.database == ":memory:":
            return True
        return _sqlite_file_exists(url.database)

    if dialect == "postgresql":
        query = sa.text("SELECT 1 FROM pg_database WHERE datname = :name")
        # the database we are looking for might not be connectable yet, so try
        # the maintenance databases as well
        candidates: list[str | None] = [url.database, "postgres", "template1", "template0", None]
        for database in candidates:
            engine = sa.create_engine(
                _url_with_database(url, database), isolation_level="AUTOCOMMIT"
            )
            try:
                with engine.connect() as conn:
                    return bool(conn.scalar(query, {"name": url.database}))
            except (OperationalError, ProgrammingError):
                continue
            finally:
                engine.dispose()
        return False

    if dialect == "mysql":
        query = sa.text(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :name"
        )
        engine = sa.create_engine(_url_with_database(url, None))
        try:
            with engine.connect() as conn:
                return bool(conn.scalar(query, {"name": url.database}))
        finally:
            engine.dispose()

    engine = sa.create_engine(url)
    try:
        with engine.connect() as conn:
            return bool(conn.scalar(sa.text("SELECT 1")))
    except (OperationalError, ProgrammingError):
        return False
    finally:
        engine.dispose()


def create_database(url: sa.engine.url.URL) -> None:
    """Issues the CREATE DATABASE statement for ``url``."""
    dialect = url.get_dialect().name
    database = url.database

    # an in-memory sqlite database needs no creation
    if not database or database == ":memory:":
        return

    if dialect == "sqlite":
        engine = sa.create_engine(url)
        with engine.begin() as conn:
            # sqlite only writes the file header once a table is created
            conn.execute(sa.text("CREATE TABLE DB(id int)"))
            conn.execute(sa.text("DROP TABLE DB"))
        engine.dispose()
        return

    if dialect == "postgresql":
        # CREATE DATABASE cannot run inside a transaction
        engine = sa.create_engine(_url_with_database(url, "postgres"), isolation_level="AUTOCOMMIT")
        template = "CREATE DATABASE {} ENCODING 'utf8' TEMPLATE template1"
    elif dialect == "mysql":
        engine = sa.create_engine(_url_with_database(url, None))
        template = "CREATE DATABASE {} CHARACTER SET = 'utf8mb4'"
    else:
        engine = sa.create_engine(_url_with_database(url, None))
        template = "CREATE DATABASE {}"

    with engine.begin() as conn:
        name = conn.dialect.identifier_preparer.quote(database)
        conn.execute(sa.text(template.format(name)))
    engine.dispose()
