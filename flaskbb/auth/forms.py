# -*- coding: utf-8 -*-
"""
    flaskbb.auth.forms
    ~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the auth views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from flask_wtf import Form
from wtforms import (StringField, PasswordField, BooleanField, HiddenField,
                     SubmitField, SelectField)
from wtforms.validators import (DataRequired, InputRequired, Email, EqualTo,
                                regexp, ValidationError)
from flask_babelplus import lazy_gettext as _
from flaskbb.user.models import User, Group
from flaskbb.utils.recaptcha import RecaptchaField

USERNAME_RE = r'^[\w.+-]+$'
is_username = regexp(USERNAME_RE,
                     message=_("You can only use letters, numbers or dashes."))


class LoginForm(Form):
    login = StringField(_("Username or Email address"), validators=[
        DataRequired(message=_("Please enter your username or email address."))
    ])

    password = PasswordField(_("Password"), validators=[
        DataRequired(message=_("Please enter your password."))])

    recaptcha = RecaptchaField(_("Captcha"))

    remember_me = BooleanField(_("Remember me"), default=False)

    submit = SubmitField(_("Login"))


class RegisterForm(Form):
    username = StringField(_("Username"), validators=[
        DataRequired(message=_("A valid username is required.")),
        is_username])

    email = StringField(_("Email address"), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email(message=_("Invalid email address."))])

    password = PasswordField(_('Password'), validators=[
        InputRequired(),
        EqualTo('confirm_password', message=_('Passwords must match.'))])

    confirm_password = PasswordField(_('Confirm password'))

    recaptcha = RecaptchaField(_("Captcha"))

    language = SelectField(_('Language'))

    accept_tos = BooleanField(_("I accept the Terms of Service"), default=True)

    submit = SubmitField(_("Register"))

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError(_("This username is already taken."))

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if email:
            raise ValidationError(_("This email address is already taken."))

    def save(self):
        group = Group.query.filter_by(default_group=True).first()
        user = User(username=self.username.data,
                    email=self.email.data,
                    password=self.password.data,
                    date_joined=datetime.utcnow(),
                    primary_group_id=group.id,
                    language=self.language.data)
        return user.save()


class ReauthForm(Form):
    password = PasswordField(_('Password'), validators=[
        DataRequired(message=_("Please enter your password."))])

    submit = SubmitField(_("Refresh Login"))


class ForgotPasswordForm(Form):
    email = StringField(_('Email address'), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email()])

    recaptcha = RecaptchaField(_("Captcha"))

    submit = SubmitField(_("Request Password"))


class ResetPasswordForm(Form):
    token = HiddenField('Token')

    email = StringField(_('Email address'), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email()])

    password = PasswordField(_('Password'), validators=[
        InputRequired(),
        EqualTo('confirm_password', message=_('Passwords must match.'))])

    confirm_password = PasswordField(_('Confirm password'))

    submit = SubmitField(_("Reset password"))

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if not email:
            raise ValidationError(_("Wrong email address."))


class RequestActivationForm(Form):
    username = StringField(_("Username"), validators=[
        DataRequired(message=_("A valid username is required.")),
        is_username])

    email = StringField(_("Email address"), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email(message=_("Invalid email address."))])

    submit = SubmitField(_("Send Confirmation Mail"))

    def validate_email(self, field):
        self.user = User.query.filter_by(email=field.data).first()
        # check if the username matches the one found in the database
        if not self.user.username == self.username.data:
            raise ValidationError(_("User does not exist."))

        if self.user.activated is not None:
            raise ValidationError(_("User is already active."))


class AccountActivationForm(Form):
    token = StringField(_("Email confirmation token"), validators=[
        DataRequired(message=_("Please enter the token that we have sent to "
                               "you."))
    ])

    submit = SubmitField(_("Confirm Email"))
