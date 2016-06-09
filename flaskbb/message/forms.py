# -*- coding: utf-8 -*-
"""
    flaskbb.message.forms
    ~~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the message views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask_login import current_user
from flask_wtf import Form
from wtforms import StringField, TextAreaField, ValidationError, SubmitField
from wtforms.validators import DataRequired
from flask_babelplus import lazy_gettext as _

from flaskbb.user.models import User
from flaskbb.message.models import Conversation, Message


class ConversationForm(Form):
    to_user = StringField(_("Recipient"), validators=[
        DataRequired(message=_("A valid username is required."))])

    subject = StringField(_("Subject"), validators=[
        DataRequired(message=_("A Subject is required."))])

    message = TextAreaField(_("Message"), validators=[
        DataRequired(message=_("A message is required."))])

    send_message = SubmitField(_("Start Conversation"))
    save_message = SubmitField(_("Save Conversation"))

    def validate_to_user(self, field):
        user = User.query.filter_by(username=field.data).first()
        if not user:
            raise ValidationError(_("The username you entered does not "
                                    "exist."))
        if user.id == current_user.id:
            raise ValidationError(_("You cannot send a PM to yourself."))

    def save(self, from_user, to_user, user_id, unread, as_draft=False,
             shared_id=None):

        conversation = Conversation(
            subject=self.subject.data,
            draft=as_draft,
            shared_id=shared_id,
            from_user_id=from_user,
            to_user_id=to_user,
            user_id=user_id,
            unread=unread
        )
        message = Message(message=self.message.data, user_id=from_user)
        return conversation.save(message=message)


class MessageForm(Form):
    message = TextAreaField(_("Message"), validators=[
        DataRequired(message=_("A message is required."))])
    submit = SubmitField(_("Send Message"))

    def save(self, conversation, user_id, unread=False):
        """Saves the form data to the model.
        :param conversation: The Conversation object.
        :param user_id: The id from the user who sent the message.
        :param reciever: If the message should also be stored in the recievers
                         inbox.
        """
        message = Message(message=self.message.data, user_id=user_id)

        if unread:
            conversation.unread = True
            conversation.save()
        return message.save(conversation)
