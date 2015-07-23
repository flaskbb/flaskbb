# -*- coding: utf-8 -*-
"""
    flaskbb.utils.database
    ~~~~~~~~~~~~~~~~~~~~~~

    Some database helpers such as a CRUD mixin.

    :copyright: (c) 2015 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flaskbb.extensions import db


class CRUDMixin(object):
    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)

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
