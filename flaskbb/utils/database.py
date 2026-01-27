# -*- coding: utf-8 -*-
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

import pytz
import sqlalchemy as sa
import sqlalchemy.types as types
from flask_login import current_user
from flask_sqlalchemy.query import Query
from sqlalchemy.orm import declarative_mixin, declared_attr

from flaskbb.extensions import db

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


class CRUDMixin(object):
    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        return instance.save()

    def save(self):
        """Saves the object to the database."""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete the object from the database."""
        db.session.delete(self)
        db.session.commit()
        return self


class UTCDateTime(types.TypeDecorator):
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
            value = value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return value

    @t.override
    def process_result_value(
        self, value: t.Any | None, dialect: sa.Dialect
    ) -> datetime.datetime | None:
        """Way out of the database."""
        if value is not None:
            value = value.replace(tzinfo=datetime.timezone.utc)
        return value


class HideableQuery(Query):
    _with_hidden: bool = False

    def __new__(cls, *args, **kwargs):
        obj = super(HideableQuery, cls).__new__(cls)
        include_hidden: bool = kwargs.pop("_with_hidden", False)
        has_view_hidden = current_user and current_user.permissions.get(
            "viewhidden", False
        )
        obj._with_hidden = include_hidden or has_view_hidden
        if args or kwargs:
            super(HideableQuery, obj).__init__(*args, **kwargs)
            return obj.filter_by(hidden=False) if not obj._with_hidden else obj
        return obj

    def __init__(self, *args, **kwargs):
        pass

    def with_hidden(self):
        return self.__class__(
            self._only_full_mapper_zero("get"),
            session=db.session(),
            _with_hidden=True,
        )

    def _get(self, *args, **kwargs):
        return super(HideableQuery, self).filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        obj = self.with_hidden()._get(*args, **kwargs).first()
        return obj if obj is None or self._with_hidden or not obj.hidden else None


@declarative_mixin
class HideableMixin(object):
    query_class = HideableQuery

    hidden = db.Column(db.Boolean, default=False, nullable=True)
    hidden_at = db.Column(UTCDateTime(timezone=True), nullable=True)

    @declared_attr
    def hidden_by_id(cls):  # noqa: B902
        return db.Column(
            db.Integer,
            db.ForeignKey("users.id", name="fk_{}_hidden_by".format(cls.__name__)),
            nullable=True,
        )

    @declared_attr
    def hidden_by(cls):  # noqa: B902
        return db.relationship("User", uselist=False, foreign_keys=[cls.hidden_by_id])

    def hide(self, user, *args, **kwargs):
        from flaskbb.utils.helpers import time_utcnow

        self.hidden_by = user
        self.hidden = True
        self.hidden_at = time_utcnow()
        return self

    def unhide(self, *args, **kwargs):
        self.hidden_by = None
        self.hidden = False
        self.hidden_at = None
        return self


class HideableCRUDMixin(HideableMixin, CRUDMixin):
    pass


def try_commit(session, message="Error while saving"):
    try:
        session.commit()
    except Exception:
        raise PersistenceError(message)
