# -*- coding: utf-8 -*-
"""
    flaskbb.user.forms
    ~~~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the user views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask_login import current_user
from flask_wtf import Form
from wtforms import (StringField, PasswordField, TextAreaField, SelectField,
                     ValidationError, SubmitField)
from wtforms.validators import (Length, DataRequired, InputRequired, Email,
                                EqualTo, regexp, Optional, URL)
from flask_babelex import lazy_gettext as _

from flaskbb.user.models import User, PrivateMessage
from flaskbb.extensions import db
from flaskbb.utils.widgets import SelectBirthdayWidget
from flaskbb.utils.fields import BirthdayField
from flaskbb.utils.helpers import check_image


class GeneralSettingsForm(Form):
    # The choices for those fields will be generated in the user view
    # because we cannot access the current_app outside of the context
    language = SelectField(_("Language"))
    theme = SelectField(_("Theme"))

    submit = SubmitField(_("Save"))


class ChangeEmailForm(Form):
    old_email = StringField(_("Old E-Mail Address"), validators=[
        DataRequired(message=_("A E-Mail Address is required.")),
        Email(message=_("Invalid E-Mail Address."))])

    new_email = StringField(_("New E-Mail Address"), validators=[
        InputRequired(),
        EqualTo('confirm_new_email', message=_("E-Mails must match.")),
        Email(message=_("Invalid E-Mail Address."))])

    confirm_new_email = StringField(_("Confirm E-Mail Address"), validators=[
        Email(message=_("Invalid E-Mail Address."))])

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
            raise ValidationError(_("This E-Mail Address is already taken."))


class ChangePasswordForm(Form):
    old_password = PasswordField(_("Old Password"), validators=[
        DataRequired(message=_("Password required"))])

    new_password = PasswordField(_('Password'), validators=[
        InputRequired(),
        EqualTo('confirm_new_password', message=_('Passwords must match.'))])

    confirm_new_password = PasswordField(_('Confirm New Password'))

    submit = SubmitField(_("Save"))

    def validate_old_password(self, field):
        if not current_user.check_password(field.data):
            raise ValidationError(_("Old Password is wrong."))


class ChangeUserDetailsForm(Form):
    birthday = BirthdayField(_("Birthday"), format="%d %m %Y",
                             validators=[Optional()],
                             widget=SelectBirthdayWidget())

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


class NewMessageForm(Form):
    to_user = StringField(_("To User"), validators=[
        DataRequired(message=_("A Username is required."))])

    subject = StringField(_("Subject"), validators=[
        DataRequired(message=_("A Subject is required."))])

    message = TextAreaField(_("Message"), validators=[
        DataRequired(message=_("A Message is required."))])

    send_message = SubmitField(_("Send Message"))
    save_message = SubmitField(_("Save Message"))

    def validate_to_user(self, field):
        user = User.query.filter_by(username=field.data).first()
        if not user:
            raise ValidationError(_("The Username you entered doesn't exist"))
        if user.id == current_user.id:
            raise ValidationError(_("You cannot send a PM to yourself."))

    def save(self, from_user, to_user, user_id, unread, as_draft=False):
        message = PrivateMessage(
            subject=self.subject.data,
            message=self.message.data,
            unread=unread)

        if as_draft:
            return message.save(from_user, to_user, user_id, draft=True)
        return message.save(from_user, to_user, user_id)


class EditMessageForm(NewMessageForm):
    pass
