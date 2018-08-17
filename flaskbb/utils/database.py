# -*- coding: utf-8 -*-
"""
    flaskbb.utils.database
    ~~~~~~~~~~~~~~~~~~~~~~

    Some database helpers such as a CRUD mixin.

    :copyright: (c) 2015 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
import pytz
from flask_login import current_user
from flask_sqlalchemy import BaseQuery
from sqlalchemy.ext.declarative import declared_attr
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


class UTCDateTime(db.TypeDecorator):
    impl = db.DateTime

    def process_bind_param(self, value, dialect):
        """Way into the database."""
        if value is not None:
            # store naive datetime for sqlite and mysql
            if dialect.name in ("sqlite", "mysql"):
                return value.replace(tzinfo=None)

            return value.astimezone(pytz.UTC)

    def process_result_value(self, value, dialect):
        """Way out of the database."""
        # convert naive datetime to non naive datetime
        if dialect.name in ("sqlite", "mysql") and value is not None:
            return value.replace(tzinfo=pytz.UTC)

        # other dialects are already non-naive
        return value


class HideableQuery(BaseQuery):

    def __new__(cls, *args, **kwargs):
        inst = super(HideableQuery, cls).__new__(cls)
        include_hidden = kwargs.pop("_with_hidden", False)
        has_view_hidden = current_user and current_user.permissions.get(
            "viewhidden", False
        )
        with_hidden = include_hidden or has_view_hidden
        if args or kwargs:
            super(HideableQuery, inst).__init__(*args, **kwargs)
            entity = inst._mapper_zero().class_
            return inst.filter(
                entity.hidden != True
            ) if not with_hidden else inst
        return inst

    def __init__(self, *args, **kwargs):
        pass

    def with_hidden(self):
        return self.__class__(
            db.class_mapper(self._mapper_zero().class_),
            session=db.session(),
            _with_hidden=True,
        )

    def _get(self, *args, **kwargs):
        return super(HideableQuery, self).get(*args, **kwargs)

    def get(self, *args, **kwargs):
        include_hidden = kwargs.pop("include_hidden", False)
        obj = self.with_hidden()._get(*args, **kwargs)
        return obj if obj is not None and (
            include_hidden or not obj.hidden
        ) else None


class HideableMixin(object):
    query_class = HideableQuery

    hidden = db.Column(db.Boolean, default=False, nullable=True)
    hidden_at = db.Column(UTCDateTime(timezone=True), nullable=True)

    @declared_attr
    def hidden_by_id(cls):  # noqa: B902
        return db.Column(
            db.Integer,
            db.ForeignKey(
                "users.id", name="fk_{}_hidden_by".format(cls.__name__)
            ),
            nullable=True,
        )

    @declared_attr
    def hidden_by(cls):  # noqa: B902
        return db.relationship(
            "User", uselist=False, foreign_keys=[cls.hidden_by_id]
        )

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
