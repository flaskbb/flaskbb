# -*- coding: utf-8 -*-
"""
    flaskbb.auth.forms
    ~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the auth views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging

from flask_babelplus import lazy_gettext as _
from wtforms import (
    BooleanField,
    HiddenField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    InputRequired,
    regexp,
)

from flaskbb.utils.fields import RecaptchaField
from flaskbb.utils.forms import FlaskBBForm

logger = logging.getLogger(__name__)

USERNAME_RE = r"^[\w.+-]+$"
is_valid_username = regexp(
    USERNAME_RE, message=_("You can only use letters, numbers or dashes.")
)


class LoginForm(FlaskBBForm):
    login = StringField(
        _("Username or Email address"),
        validators=[
            DataRequired(
                message=_("Please enter your username or email address.")
            )
        ],
    )

    password = PasswordField(
        _("Password"),
        validators=[DataRequired(message=_("Please enter your password."))],
    )

    remember_me = BooleanField(_("Remember me"), default=False)

    submit = SubmitField(_("Login"))
    recaptcha = HiddenField(_("Captcha"))


class LoginRecaptchaForm(LoginForm):
    recaptcha = RecaptchaField(_("Captcha"))


class RegisterForm(FlaskBBForm):
    username = StringField(
        _("Username"),
        validators=[
            DataRequired(message=_("A valid username is required")),
            is_valid_username,
        ],
    )

    email = StringField(
        _("Email address"),
        validators=[
            DataRequired(message=_("A valid email address is required.")),
            Email(message=_("Invalid email address.")),
        ],
    )

    password = PasswordField(
        _("Password"),
        validators=[
            InputRequired(),
            EqualTo("confirm_password", message=_("Passwords must match.")),
        ],
    )

    confirm_password = PasswordField(_("Confirm password"))

    recaptcha = RecaptchaField(_("Captcha"))

    language = SelectField(_("Language"))

    accept_tos = BooleanField(
        _("I accept the Terms of Service"),
        validators=[DataRequired(message=_("Please accept the TOS."))],
        default=True,
    )

    submit = SubmitField(_("Register"))


class ReauthForm(FlaskBBForm):
    password = PasswordField(
        _("Password"),
        validators=[DataRequired(message=_("Please enter your password."))],
    )

    submit = SubmitField(_("Refresh Login"))


class ForgotPasswordForm(FlaskBBForm):
    email = StringField(
        _("Email address"),
        validators=[
            DataRequired(message=_("A valid email address is required.")),
            Email(),
        ],
    )

    recaptcha = RecaptchaField(_("Captcha"))

    submit = SubmitField(_("Request Password"))


class ResetPasswordForm(FlaskBBForm):
    token = HiddenField("Token")

    email = StringField(
        _("Email address"),
        validators=[
            DataRequired(message=_("A valid email address is required.")),
            Email(),
        ],
    )

    password = PasswordField(
        _("Password"),
        validators=[
            InputRequired(),
            EqualTo("confirm_password", message=_("Passwords must match.")),
        ],
    )

    confirm_password = PasswordField(_("Confirm password"))

    submit = SubmitField(_("Reset password"))


class RequestActivationForm(FlaskBBForm):
    username = StringField(
        _("Username"),
        validators=[
            DataRequired(message=_("A valid username is required.")),
            is_valid_username,
        ],
    )

    email = StringField(
        _("Email address"),
        validators=[
            DataRequired(message=_("A valid email address is required.")),
            Email(message=_("Invalid email address.")),
        ],
    )

    submit = SubmitField(_("Send Confirmation Mail"))


class AccountActivationForm(FlaskBBForm):
    token = StringField(
        _("Email confirmation token"),
        validators=[
            DataRequired(_("Please enter the token we have sent to you."))
        ],
    )
    submit = SubmitField(_("Confirm Email"))
