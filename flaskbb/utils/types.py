# -*- coding: utf-8 -*-
"""
    flaskbb.utils.types
    ~~~~~~~~~~~~~~~~~~~~

    Additional types for SQLAlchemy

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from sqlalchemy import types
from sqlalchemy.ext.mutable import Mutable
import json


class SetType(types.TypeDecorator):
    """
    Represents an immutable set.

    :param coerce: coercion function that ensures correct
                   type is returned

    :param separator: separator character
    """

    impl = types.Text

    def __init__(self, coerce=int, separator=" ", **kwargs):

        self.coerce = coerce
        self.separator = separator

        super(SetType, self).__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        if value is not None:
            items = [str(item).strip() for item in value]
            value = self.separator.join(item for item in items if item)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return set(self.coerce(item) for item in value.split(" "))
        return set()


class MutableSet(Mutable, set):
    @classmethod
    def coerce(cls, key, value):
        """
        Convert plain sets to MutableSet.
        """

        if not isinstance(value, MutableSet):
            if isinstance(value, set):
                return MutableSet(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def add(self, value):
        """
        Detect set add events and emit change events.
        """
        set.add(self, value)
        self.changed()

    def remove(self, value):
        """
        Detect set remove events and emit change events.
        """
        set.remove(self, value)
        self.changed()


# http://docs.sqlalchemy.org/en/rel_0_9/orm/extensions/mutable.html
class MutableDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        """
        Convert plain dictionaries to MutableDict.
        """

        if not isinstance(value, MutableDict):
            if isinstance(value, dict):
                return MutableDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        """
        Detect dictionary set events and emit change events.
        """

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        """
        Detect dictionary del events and emit change events.
        """

        dict.__delitem__(self, key)
        self.changed()


class JSONEncodedDict(types.TypeDecorator):
    """
    Represents an immutable structure as a json-encoded string.
    """

    impl = types.VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value
