# -*- coding: utf-8 -*-
"""
    flaskbb.auth.forms
    ~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the auth views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime

from flask_wtf import Form, RecaptchaField
from wtforms import (StringField, PasswordField, BooleanField, HiddenField,
                     SubmitField, SelectField)
from wtforms.validators import (DataRequired, InputRequired, Email, EqualTo,
                                regexp, ValidationError)
from flask_babelex import lazy_gettext as _
from flaskbb.user.models import User

USERNAME_RE = r'^[\w.+-]+$'
is_username = regexp(USERNAME_RE,
                     message=_("You can only use letters, numbers or dashes."))


class LoginForm(Form):
    login = StringField(_("Username or E-Mail Address"), validators=[
        DataRequired(message=_("A Username or E-Mail Address is required."))]
    )

    password = PasswordField(_("Password"), validators=[
        DataRequired(message=_("A Password is required."))])

    remember_me = BooleanField(_("Remember Me"), default=False)

    submit = SubmitField(_("Login"))


class RegisterForm(Form):
    username = StringField(_("Username"), validators=[
        DataRequired(message=_("A Username is required.")),
        is_username])

    email = StringField(_("E-Mail Address"), validators=[
        DataRequired(message=_("A E-Mail Address is required.")),
        Email(message=_("Invalid E-Mail Address."))])

    password = PasswordField(_('Password'), validators=[
        InputRequired(),
        EqualTo('confirm_password', message=_('Passwords must match.'))])

    confirm_password = PasswordField(_('Confirm Password'))


    language = SelectField(_('Language'))

    accept_tos = BooleanField(_("I accept the Terms of Service"), default=True)

    submit = SubmitField(_("Register"))

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError(_("This Username is already taken."))

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if email:
            raise ValidationError(_("This E-Mail Address is already taken."))

    def save(self):
        user = User(username=self.username.data,
                    email=self.email.data,
                    password=self.password.data,
                    date_joined=datetime.utcnow(),
                    primary_group_id=4,
                    language=self.language.data)
        return user.save()


class RegisterRecaptchaForm(RegisterForm):
    recaptcha = RecaptchaField(_("Captcha"))


class ReauthForm(Form):
    password = PasswordField(_('Password'), valdidators=[
        DataRequired(message=_("A Password is required."))])

    submit = SubmitField(_("Refresh Login"))


class ForgotPasswordForm(Form):
    email = StringField(_('E-Mail Address'), validators=[
        DataRequired(message=_("A E-Mail Address is reguired.")),
        Email()])

    submit = SubmitField(_("Request Password"))


class ResetPasswordForm(Form):
    token = HiddenField('Token')

    email = StringField(_('E-Mail Address'), validators=[
        DataRequired(message=_("A E-Mail Address is required.")),
        Email()])

    password = PasswordField(_('Password'), validators=[
        InputRequired(),
        EqualTo('confirm_password', message=_('Passwords must match.'))])

    confirm_password = PasswordField(_('Confirm Password'))

    submit = SubmitField(_("Reset Password"))

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if not email:
            raise ValidationError(_("Wrong E-Mail Address."))
