# -*- coding: utf-8 -*-
"""
    flaskbb.user.forms
    ~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the user views.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask.ext.wtf import (Form, TextField, PasswordField, Length, Required,
                           Email, EqualTo, ValidationError, regexp, DateField,
                           TextAreaField, Optional, URL, SelectField)

from flaskbb.user.models import User
from flaskbb.extensions import db
from flaskbb.utils import SelectDateWidget

IMG_RE = r'^[^/\\]\.(?:jpg|gif|png)'

is_image = regexp(IMG_RE,
                  message=("Only jpg, jpeg, png and gifs are allowed!"))


class ChangeEmailForm(Form):
    old_email = TextField("Old E-Mail Address", validators=[
        Required(message="Email adress required"),
        Email(message="This email is invalid")])

    new_email = TextField("New E-Mail Address", validators=[
        Required(message="Email adress required"),
        Email(message="This email is invalid")])

    confirm_new_email = TextField("Confirm E-Mail Address", validators=[
        Required(message="Email adress required"),
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
        Required(message="Password required")])

    new_password = PasswordField("New Password", validators=[
        Required(message="Password required")])

    confirm_new_password = PasswordField("Confirm New Password", validators=[
        Required(message="Password required"),
        EqualTo("new_password", message="Passwords do not match")])


class ChangeUserDetailsForm(Form):
    birthday = DateField("Your Birthday", format="%d %m %Y",
        widget=SelectDateWidget(), validators=[
        Optional()])

    gender = SelectField("Gender", default="None", choices=[
        ("None", ""),
        ("Male", "Male"),
        ("Female", "Female")])

    location = TextField("Location", validators=[
        Optional()])

    website = TextField("Website", validators=[
        Optional(), URL()])

    avatar = TextField("Avatar", validators=[
        Optional(), URL()])

    signature = TextAreaField("Forum Signature", validators=[
        Optional()])

    notes = TextAreaField("Notes", validators=[
        Optional(), Length(min=0, max=5000)])
