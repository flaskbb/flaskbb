# -*- coding: utf-8 -*-
"""
    flaskbb.utils.database
    ~~~~~~~~~~~~~~~~~~~~~~

    Some database helpers such as a CRUD mixin.

    :copyright: (c) 2015 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import pytz
from sqlalchemy.ext.declarative import declared_attr

from flaskbb.extensions import db


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


def primary_key(type=db.Integer):
    return db.Column(type, primary_key=True, nullable=False)


class PermissionBase(object):
    id = primary_key()
    value = db.Column(db.Boolean(), default=False)

    @declared_attr
    def permission_id(cls):
        return db.Column(db.ForeignKey('permissions.id'), nullable=False)

    @declared_attr
    def permission(cls):
        return db.relationship('Permission', uselist=False, lazy='joined')


class HasPermissions(object):

    @declared_attr
    def permissions_(cls):
        perms_name = "{}Permission".format(cls.__name__)
        table_name = "{}_permissions".format(cls.__tablename__)
        parent_id = db.Column(db.ForeignKey("{}.id".format(cls.__tablename__)), nullable=False)

        def repr(self):
            return "<{}Permission {} value={}>".format(
                cls.__name__, self.permission.name, self.value
            )

        cls.Permission = type(
            perms_name, (PermissionBase, db.Model),
            {'parent_id': parent_id,
             '__tablename__': table_name,
             '__repr__': repr}
        )
        return db.relationship(cls.Permission, backref='parent', lazy="joined")
