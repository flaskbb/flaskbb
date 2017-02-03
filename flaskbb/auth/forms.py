# -*- coding: utf-8 -*-
"""
    flaskbb.auth.forms
    ~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the auth views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, HiddenField,
                     SubmitField, SelectField)
from wtforms.validators import (DataRequired, InputRequired, Email, EqualTo,
                                regexp, ValidationError)
from flask_babelplus import lazy_gettext as _

from flaskbb.user.models import User
from flaskbb.utils.settings import flaskbb_config
from flaskbb.utils.helpers import time_utcnow
from flaskbb.utils.fields import RecaptchaField

USERNAME_RE = r'^[\w.+-]+$'
is_valid_username = regexp(
    USERNAME_RE, message=_("You can only use letters, numbers or dashes.")
)


class LoginForm(FlaskForm):
    login = StringField(_("Username or Email address"), validators=[
        DataRequired(message=_("Please enter your username or email address."))
    ])

    password = PasswordField(_("Password"), validators=[
        DataRequired(message=_("Please enter your password."))])

    remember_me = BooleanField(_("Remember me"), default=False)

    submit = SubmitField(_("Login"))


class LoginRecaptchaForm(LoginForm):
    recaptcha = RecaptchaField(_("Captcha"))


class RegisterForm(FlaskForm):
    username = StringField(_("Username"), validators=[
        DataRequired(message=_("A valid username is required")),
        is_valid_username])

    email = StringField(_("Email address"), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email(message=_("Invalid email address."))])

    password = PasswordField(_('Password'), validators=[
        InputRequired(),
        EqualTo('confirm_password', message=_('Passwords must match.'))])

    confirm_password = PasswordField(_('Confirm password'))

    recaptcha = RecaptchaField(_("Captcha"))

    language = SelectField(_('Language'))

    accept_tos = BooleanField(_("I accept the Terms of Service"), validators=[
        DataRequired(message=_("Please accept the TOS."))], default=True)

    submit = SubmitField(_("Register"))

    def validate_username(self, field):
        # would through an out of context error if used with validators.Length
        min_length = flaskbb_config["AUTH_USERNAME_MIN_LENGTH"]
        max_length = flaskbb_config["AUTH_USERNAME_MAX_LENGTH"]
        blacklist = [w.strip() for w in
                     flaskbb_config["AUTH_USERNAME_BLACKLIST"].split(",")]

        if len(field.data) < min_length or len(field.data) > max_length:
            raise ValidationError(_(
                "Username must be between %(min)s and %(max)s characters long.",
                min=min_length, max=max_length)
            )
        if field.data.lower() in blacklist:
            raise ValidationError(_(
                "This is a system reserved name. Choose a different one.")
            )
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError(_("This username is already taken."))

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if email:
            raise ValidationError(_("This email address is already taken."))

    def save(self):
        user = User(username=self.username.data,
                    email=self.email.data,
                    password=self.password.data,
                    date_joined=time_utcnow(),
                    primary_group_id=4,
                    language=self.language.data)
        return user.save()


class ReauthForm(FlaskForm):
    password = PasswordField(_('Password'), validators=[
        DataRequired(message=_("Please enter your password."))])

    submit = SubmitField(_("Refresh Login"))


class ForgotPasswordForm(FlaskForm):
    email = StringField(_('Email address'), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email()])

    recaptcha = RecaptchaField(_("Captcha"))

    submit = SubmitField(_("Request Password"))


class ResetPasswordForm(FlaskForm):
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


class RequestActivationForm(FlaskForm):
    username = StringField(_("Username"), validators=[
        DataRequired(message=_("A valid username is required.")),
        is_valid_username])

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


class AccountActivationForm(FlaskForm):
    token = StringField(_("Email confirmation token"), validators=[
        DataRequired(message=_("Please enter the token that we have sent to "
                               "you."))
    ])

    submit = SubmitField(_("Confirm Email"))
