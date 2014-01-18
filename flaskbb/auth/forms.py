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
from wtforms import TextField, PasswordField, BooleanField, HiddenField
from wtforms.validators import Required, Email, EqualTo, regexp, ValidationError

from flaskbb.user.models import User

USERNAME_RE = r'^[\w.+-]+$'
is_username = regexp(USERNAME_RE,
                     message=("You can only use letters, numbers or dashes"))


class LoginForm(Form):
    login = TextField("Username or E-Mail", validators=[
        Required(message="You must provide an email adress or username")])

    password = PasswordField("Password", validators=[
        Required(message="Password required")])

    remember_me = BooleanField("Remember Me", default=False)


class RegisterForm(Form):
    username = TextField("Username", validators=[
        Required(message="Username required"),
        is_username])

    email = TextField("E-Mail", validators=[
        Required(message="Email adress required"),
        Email(message="This email is invalid")])

    password = PasswordField("Password", validators=[
        Required(message="Password required")])

    confirm_password = PasswordField("Confirm Password", validators=[
        Required(message="Confirm Password required"),
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
    password = PasswordField('Password', [Required()])


class ForgotPasswordForm(Form):
    email = TextField('Email', validators=[
        Required(message="Email reguired"),
        Email()])


class ResetPasswordForm(Form):
    token = HiddenField('Token')

    email = TextField('Email', validators=[
        Required(),
        Email()])

    password = PasswordField('Password', validators=[
        Required()])

    confirm_password = PasswordField('Confirm password', validators=[
        Required(),
        EqualTo('password', message='Passwords must match')])

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if not email:
            raise ValidationError("Wrong E-Mail.")
