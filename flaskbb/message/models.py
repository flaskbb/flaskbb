# -*- coding: utf-8 -*-
"""
    flaskbb.message.models
    ~~~~~~~~~~~~~~~~~~~~~~

    The models for the conversations and messages are located here.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from sqlalchemy_utils import UUIDType

from flaskbb.extensions import db
from flaskbb.utils.database import CRUDMixin


class Conversation(db.Model, CRUDMixin):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    shared_id = db.Column(UUIDType, nullable=False)
    subject = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=datetime.utcnow())
    trash = db.Column(db.Boolean, nullable=False, default=False)
    draft = db.Column(db.Boolean, nullable=False, default=False)
    unread = db.Column(db.Boolean, nullable=False, default=True)

    messages = db.relationship(
        "Message", lazy="joined", backref="conversation",
        primaryjoin="Message.conversation_id == Conversation.id",
        order_by="asc(Message.id)",
        cascade="all, delete-orphan"
    )

    # this is actually the users message box
    user = db.relationship("User", lazy="joined", foreign_keys=[user_id])
    # the user to whom the conversation is addressed
    to_user = db.relationship("User", lazy="joined", foreign_keys=[to_user_id])
    # the user who sent the message
    from_user = db.relationship("User", lazy="joined",
                                foreign_keys=[from_user_id])

    @property
    def first_message(self):
        """Returns the first message object."""
        return self.messages[0]

    @property
    def last_message(self):
        """Returns the last message object."""
        return self.messages[-1]

    def save(self, message=None):
        """Saves a conversation and returns the saved conversation object.

        :param message: If given, it will also save the message for the
                        conversation. It expects a Message object.
        """
        if message is not None:
            # create the conversation
            self.date_created = datetime.utcnow()
            db.session.add(self)
            db.session.commit()

            # create the actual message for the conversation
            message.save(self)
            return self

        db.session.add(self)
        db.session.commit()
        return self


class Message(db.Model, CRUDMixin):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"),
                                nullable=False)

    # the user who wrote the message
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())

    user = db.relationship("User", lazy="joined")

    def save(self, conversation=None):
        """Saves a private message.

        :param conversation: The  conversation to which the message
                             belongs to.
        """
        if conversation is not None:
            self.conversation_id = conversation.id
            self.date_created = datetime.utcnow()

        db.session.add(self)
        db.session.commit()
        return self
