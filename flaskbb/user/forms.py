# -*- coding: utf-8 -*-
"""
    flaskbb.user.forms
    ~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the user views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, TextAreaField, SelectField,
                     ValidationError, SubmitField)
from wtforms.validators import (Length, DataRequired, InputRequired, Email,
                                EqualTo, Optional, URL)
from flask_babelplus import lazy_gettext as _

from flaskbb.user.models import User
from flaskbb.extensions import db
from flaskbb.utils.fields import BirthdayField
from flaskbb.utils.helpers import check_image


logger = logging.getLogger(__name__)


class GeneralSettingsForm(FlaskForm):
    # The choices for those fields will be generated in the user view
    # because we cannot access the current_app outside of the context
    language = SelectField(_("Language"))
    theme = SelectField(_("Theme"))

    submit = SubmitField(_("Save"))


class ChangeEmailForm(FlaskForm):
    old_email = StringField(_("Old email address"), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email(message=_("Invalid email address."))])

    new_email = StringField(_("New email address"), validators=[
        InputRequired(),
        EqualTo('confirm_new_email', message=_("Email addresses must match.")),
        Email(message=_("Invalid email address."))])

    confirm_new_email = StringField(_("Confirm email address"), validators=[
        Email(message=_("Invalid email address."))])

    submit = SubmitField(_("Save"))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs['obj'] = self.user
        super(ChangeEmailForm, self).__init__(*args, **kwargs)

    def validate_email(self, field):
        user = User.query.filter(db.and_(
                                 User.email.like(field.data),
                                 db.not_(User.id == self.user.id))).first()
        if user:
            raise ValidationError(_("This email address is already taken."))


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(_("Password"), validators=[
        DataRequired(message=_("Please enter your password."))])

    new_password = PasswordField(_('New password'), validators=[
        InputRequired(),
        EqualTo('confirm_new_password', message=_('New passwords must match.'))
    ])

    confirm_new_password = PasswordField(_('Confirm new password'))

    submit = SubmitField(_("Save"))

    def validate_old_password(self, field):
        if not current_user.check_password(field.data):
            raise ValidationError(_("Old password is wrong."))


class ChangeUserDetailsForm(FlaskForm):
    birthday = BirthdayField(_("Birthday"), format="%d %m %Y", validators=[
        Optional()])

    gender = SelectField(_("Gender"), default="None", choices=[
        ("None", ""),
        ("Male", _("Male")),
        ("Female", _("Female"))])

    location = StringField(_("Location"), validators=[
        Optional()])

    website = StringField(_("Website"), validators=[
        Optional(), URL()])

    avatar = StringField(_("Avatar"), validators=[
        Optional(), URL()])

    signature = TextAreaField(_("Forum Signature"), validators=[
        Optional()])

    notes = TextAreaField(_("Notes"), validators=[
        Optional(), Length(min=0, max=5000)])

    submit = SubmitField(_("Save"))

    def validate_birthday(self, field):
        if field.data is None:
            return True

    def validate_avatar(self, field):
        if field.data is not None:
            error, status = check_image(field.data)
            if error is not None:
                raise ValidationError(error)
            return status
