# -*- coding: utf-8 -*-
"""
    flaskbb.pms.forms
    ~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the pm views.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask.ext.wtf import Form
from wtforms import TextField, TextAreaField, ValidationError
from wtforms.validators import Required

from flask.ext.login import current_user

from flaskbb.user.models import User
from flaskbb.pms.models import PrivateMessage


class NewMessage(Form):
    to_user = TextField("To User", validators=[
        Required(message="A username is required.")])
    subject = TextField("Subject", validators=[
        Required(message="A subject is required.")])
    message = TextAreaField("Message", validators=[
        Required(message="A message is required.")])

    def validate_to_user(self, field):
        user = User.query.filter_by(username=field.data).first()
        if not user:
            raise ValidationError("The username you have entered doesn't exist")
        if user.id == current_user.id:
            raise ValidationError("You cannot send a PM to yourself.")

    def save(self, from_user, to_user, user_id, as_draft=False):
        message = PrivateMessage(
            subject=self.subject.data,
            message=self.message.data)

        if as_draft:
            return message.save(from_user, to_user, user_id, draft=True)
        return message.save(from_user, to_user, user_id)
