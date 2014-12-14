# -*- coding: utf-8 -*-
"""
    flaskbb.auth.forms
    ~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the auth views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from flask.ext.wtf import Form, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, HiddenField
from wtforms.validators import (DataRequired, Email, EqualTo, regexp,
                                ValidationError)

from flaskbb.user.models import User

USERNAME_RE = r'^[\w.+-]+$'
is_username = regexp(USERNAME_RE,
                     message=("You can only use letters, numbers or dashes"))


class LoginForm(Form):
    login = StringField("Username or E-Mail", validators=[
        DataRequired(message="You must provide an email adress or username")])

    password = PasswordField("Password", validators=[
        DataRequired(message="Password required")])

    remember_me = BooleanField("Remember Me", default=False)


class RegisterForm(Form):
    username = StringField("Username", validators=[
        DataRequired(message="Username required"),
        is_username])

    email = StringField("E-Mail", validators=[
        DataRequired(message="Email adress required"),
        Email(message="This email is invalid")])

    password = PasswordField("Password", validators=[
        DataRequired(message="Password required")])

    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(message="Confirm Password required"),
        EqualTo("password", message="Passwords do not match")])

    accept_tos = BooleanField("Accept Terms of Service", default=True)

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError("This username is taken")

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if email:
            raise ValidationError("This email is taken")

    def save(self):
        user = User(username=self.username.data,
                    email=self.email.data,
                    password=self.password.data,
                    date_joined=datetime.utcnow(),
                    primary_group_id=4)
        return user.save()


class RegisterRecaptchaForm(RegisterForm):
    recaptcha = RecaptchaField("Captcha")


class ReauthForm(Form):
    password = PasswordField('Password', valdidators=[
        DataRequired()])


class ForgotPasswordForm(Form):
    email = StringField('Email', validators=[
        DataRequired(message="Email reguired"),
        Email()])


class ResetPasswordForm(Form):
    token = HiddenField('Token')

    email = StringField('Email', validators=[
        DataRequired(),
        Email()])

    password = PasswordField('Password', validators=[
        DataRequired()])

    confirm_password = PasswordField('Confirm password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')])

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if not email:
            raise ValidationError("Wrong E-Mail.")
