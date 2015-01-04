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
from flask.ext.babel import lazy_gettext as _

from flaskbb.user.models import User

USERNAME_RE = r'^[\w.+-]+$'
is_username = regexp(USERNAME_RE,
                     message=_("You can only use letters, numbers or dashes"))


class LoginForm(Form):
    login = StringField(_("Username or E-Mail"), validators=[
        DataRequired(message=_("You must provide an email adress or username"))]
    )

    password = PasswordField(_("Password"), validators=[
        DataRequired(message=_("Password required"))])

    remember_me = BooleanField(_("Remember Me"), default=False)


class RegisterForm(Form):
    username = StringField(_("Username"), validators=[
        DataRequired(message=_("Username required")),
        is_username])

    email = StringField(_("E-Mail"), validators=[
        DataRequired(message=_("E-Mail required")),
        Email(message=_("This E-Mail is invalid"))])

    password = PasswordField(_("Password"), validators=[
        DataRequired(message=_("Password required"))])

    confirm_password = PasswordField(_("Confirm Password"), validators=[
        DataRequired(message=_("Confirm Password required")),
        EqualTo("password", message=_("Passwords do not match"))])

    accept_tos = BooleanField(_("I accept the Terms of Service"), default=True)

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError(_("This username is taken"))

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if email:
            raise ValidationError(_("This email is taken"))

    def save(self):
        user = User(username=self.username.data,
                    email=self.email.data,
                    password=self.password.data,
                    date_joined=datetime.utcnow(),
                    primary_group_id=4)
        return user.save()


class RegisterRecaptchaForm(RegisterForm):
    recaptcha = RecaptchaField(_("Captcha"))


class ReauthForm(Form):
    password = PasswordField(_('Password'), valdidators=[
        DataRequired()])


class ForgotPasswordForm(Form):
    email = StringField(_('E-Mail'), validators=[
        DataRequired(message=("E-Mail reguired")),
        Email()])


class ResetPasswordForm(Form):
    token = HiddenField('Token')

    email = StringField(_('E-Mail'), validators=[
        DataRequired(),
        Email()])

    password = PasswordField(_('Password'), validators=[
        DataRequired()])

    confirm_password = PasswordField(_('Confirm password'), validators=[
        DataRequired(),
        EqualTo('password', message=_('Passwords do not match'))])

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if not email:
            raise ValidationError(_("Wrong E-Mail."))
