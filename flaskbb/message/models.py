from datetime import datetime

from sqlalchemy_utils import UUIDType

from flaskbb.extensions import db


class Conversation(db.Model):
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
        "Message", lazy="dynamic", backref="conversation",
        primaryjoin="Message.conversation_id == Conversation.id",
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

    def save(self, message=None, user_id=None, from_user=None, to_user=None):
        """Saves a conversation.

        :param message: The Message object.
        :param user_id: The senders user id - This is the id to which user the
                        conversation belongs.
        :param from_user: The user who has created the conversation
        :param to_user: The user who should recieve the conversation
        """
        if self.id:
            db.session.add(self)
            db.session.commit()
            return self

        if message is not None:
            # create the conversation
            self.user_id = user_id
            self.from_user_id = from_user
            self.to_user_id = to_user
            self.date_created = datetime.utcnow()

            db.session.add(self)
            db.session.commit()

            # create the actual message for the conversation
            message.save(self)
            return self

        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Deletes a private message"""

        db.session.delete(self)
        db.session.commit()
        return self


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"),
                                nullable=False)

    # the user who wrote the message
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow())

    user = db.relationship("User", lazy="joined")

    def save(self, conversation):
        """Saves a private message.

        :param conversation_id: The id of the conversation to which the message
                                belongs to.
        """
        self.conversation_id = conversation.id
        self.date_created = datetime.utcnow()

        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Deletes a private message"""

        db.session.delete(self)
        db.session.commit()
        return self
