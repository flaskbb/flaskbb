# -*- coding: utf-8 -*-
"""
    flaskbb.user.forms
    ~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the user views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging

from flask_babelplus import lazy_gettext as _
from wtforms import (
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
    DateField,
)
from wtforms.validators import (
    URL,
    DataRequired,
    Email,
    EqualTo,
    InputRequired,
    Length,
    Optional,
)

from flaskbb.utils.forms import FlaskBBForm

from ..core.user.update import (
    EmailUpdate,
    PasswordUpdate,
    SettingsUpdate,
    UserDetailsChange,
)

logger = logging.getLogger(__name__)


class GeneralSettingsForm(FlaskBBForm):
    # The choices for those fields will be generated in the user view
    # because we cannot access the current_app outside of the context
    language = SelectField(_("Language"))
    theme = SelectField(_("Theme"))
    submit = SubmitField(_("Save"))

    def as_change(self):
        return SettingsUpdate(language=self.language.data, theme=self.theme.data)


class ChangeEmailForm(FlaskBBForm):
    old_email = StringField(
        _("Old email address"),
        validators=[
            DataRequired(message=_("A valid email address is required.")),
            Email(message=_("Invalid email address.")),
        ],
    )
    new_email = StringField(
        _("New email address"),
        validators=[
            InputRequired(),
            EqualTo("confirm_new_email", message=_("Email addresses must match.")),
            Email(message=_("Invalid email address.")),
        ],
    )
    confirm_new_email = StringField(
        _("Confirm email address"),
        validators=[Email(message=_("Invalid email address."))],
    )
    submit = SubmitField(_("Save"))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs["obj"] = self.user
        super(ChangeEmailForm, self).__init__(*args, **kwargs)

    def as_change(self):
        return EmailUpdate(old_email=self.old_email.data, new_email=self.new_email.data)


class ChangePasswordForm(FlaskBBForm):
    old_password = PasswordField(
        _("Password"),
        validators=[DataRequired(message=_("Please enter your password."))],
    )
    new_password = PasswordField(
        _("New password"),
        validators=[
            InputRequired(),
            EqualTo("confirm_new_password", message=_("New passwords must match.")),
        ],
    )
    confirm_new_password = PasswordField(_("Confirm new password"))
    submit = SubmitField(_("Save"))

    def as_change(self):
        return PasswordUpdate(
            new_password=self.new_password.data, old_password=self.old_password.data
        )


class ChangeUserDetailsForm(FlaskBBForm):
    birthday = DateField(_("Birthday"), format="%Y-%m-%d", validators=[Optional()])
    gender = StringField(_("Gender"), validators=[Optional()])
    location = StringField(_("Location"), validators=[Optional()])
    website = StringField(_("Website"), validators=[Optional(), URL()])
    avatar = StringField(_("Avatar"), validators=[Optional(), URL()])
    signature = TextAreaField(_("Forum Signature"), validators=[Optional()])
    notes = TextAreaField(_("Notes"), validators=[Optional(), Length(min=0, max=5000)])
    submit = SubmitField(_("Save"))

    def validate_birthday(self, field):
        if field.data is None:
            return True

    def as_change(self):
        return UserDetailsChange(
            birthday=self.birthday.data,
            gender=self.gender.data,
            location=self.location.data,
            website=self.website.data,
            avatar=self.avatar.data,
            signature=self.signature.data,
            notes=self.notes.data,
        )
