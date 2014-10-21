# -*- coding: utf-8 -*-
"""
    flaskbb.user.forms
    ~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the user views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask.ext.login import current_user
from flask.ext.wtf import Form
from wtforms import (StringField, PasswordField, DateField, TextAreaField,
                     SelectField, ValidationError)
from wtforms.validators import (Length, DataRequired, Email, EqualTo, regexp,
                                Optional, URL)

from flaskbb.user.models import User, PrivateMessage
from flaskbb.extensions import db
from flaskbb.utils.widgets import SelectDateWidget


IMG_RE = r'^[^/\\]\.(?:jpg|gif|png)'

is_image = regexp(IMG_RE,
                  message=("Only jpg, jpeg, png and gifs are allowed!"))


class GeneralSettingsForm(Form):
    # The choices for those fields will be generated in the user view
    # because we cannot access the current_app outside of the context
    #language = SelectField("Language")
    theme = SelectField("Theme")


class ChangeEmailForm(Form):
    old_email = StringField("Old E-Mail Address", validators=[
        DataRequired(message="Email address required"),
        Email(message="This email is invalid")])

    new_email = StringField("New E-Mail Address", validators=[
        DataRequired(message="Email address required"),
        Email(message="This email is invalid")])

    confirm_new_email = StringField("Confirm E-Mail Address", validators=[
        DataRequired(message="Email adress required"),
        Email(message="This email is invalid"),
        EqualTo("new_email", message="E-Mails do not match")])

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs['obj'] = self.user
        super(ChangeEmailForm, self).__init__(*args, **kwargs)

    def validate_email(self, field):
        user = User.query.filter(db.and_(
                                 User.email.like(field.data),
                                 db.not_(User.id == self.user.id))).first()
        if user:
            raise ValidationError("This email is taken")


class ChangePasswordForm(Form):
    old_password = PasswordField("Old Password", validators=[
        DataRequired(message="Password required")])

    new_password = PasswordField("New Password", validators=[
        DataRequired(message="Password required")])

    confirm_new_password = PasswordField("Confirm New Password", validators=[
        DataRequired(message="Password required"),
        EqualTo("new_password", message="Passwords do not match")])


class ChangeUserDetailsForm(Form):
    # TODO: Better birthday field
    birthday = DateField("Your Birthday", format="%d %m %Y",
                         widget=SelectDateWidget(), validators=[Optional()])

    gender = SelectField("Gender", default="None", choices=[
        ("None", ""),
        ("Male", "Male"),
        ("Female", "Female")])

    location = StringField("Location", validators=[
        Optional()])

    website = StringField("Website", validators=[
        Optional(), URL()])

    avatar = StringField("Avatar", validators=[
        Optional(), URL()])

    signature = TextAreaField("Forum Signature", validators=[
        Optional()])

    notes = TextAreaField("Notes", validators=[
        Optional(), Length(min=0, max=5000)])


class NewMessageForm(Form):
    to_user = StringField("To User", validators=[
        DataRequired(message="A username is required.")])
    subject = StringField("Subject", validators=[
        DataRequired(message="A subject is required.")])
    message = TextAreaField("Message", validators=[
        DataRequired(message="A message is required.")])

    def validate_to_user(self, field):
        user = User.query.filter_by(username=field.data).first()
        if not user:
            raise ValidationError("The username you entered doesn't exist")
        if user.id == current_user.id:
            raise ValidationError("You cannot send a PM to yourself.")

    def save(self, from_user, to_user, user_id, unread, as_draft=False):
        message = PrivateMessage(
            subject=self.subject.data,
            message=self.message.data,
            unread=unread)

        if as_draft:
            return message.save(from_user, to_user, user_id, draft=True)
        return message.save(from_user, to_user, user_id)


class EditMessageForm(NewMessageForm):
    pass
