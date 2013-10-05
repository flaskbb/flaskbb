# -*- coding: utf-8 -*-
"""
    flaskbb.pms.models
    ~~~~~~~~~~~~~~~~~~~~

    This module provides the appropriate models for the pm views.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from flaskbb.extensions import db


class PrivateMessage(db.Model):
    __tablename__ = "privatemessages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    subject = db.Column(db.String)
    message = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    trash = db.Column(db.Boolean, nullable=False, default=False)
    draft = db.Column(db.Boolean, nullable=False, default=False)
    unread = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship("User", backref="pms", lazy="joined",
                           foreign_keys=[user_id])
    from_user = db.relationship("User", lazy="joined",
                                foreign_keys=[from_user_id])
    to_user = db.relationship("User", lazy="joined", foreign_keys=[to_user_id])

    def save(self, from_user=None, to_user=None, user_id=None, draft=False):
        if self.id:
            db.session.add(self)
            db.session.commit()
            return self

        if draft:
            self.draft = True

        # Add the message to the user's pm box
        self.user_id = user_id
        self.from_user_id = from_user
        self.to_user_id = to_user

        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
