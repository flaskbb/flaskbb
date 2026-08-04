"""
flaskbb.user.services.factories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Factory functions for the various FlaskBB user services.

These factories are provisional and considered private APIs.

:copyright: 2018, the FlaskBB Team.
:license: BSD, see LICENSE for more details
"""

from itertools import chain

from flask import current_app
from flask_login import current_user

from ...extensions import db, pluggy
from ...utils.helpers import get_available_languages, get_available_themes
from ..forms import (
    ChangeAvatarForm,
    ChangeEmailForm,
    ChangePasswordForm,
    ChangeUserDetailsForm,
    GeneralSettingsForm,
)
from .update import (
    DefaultAvatarUpdateHandler,
    DefaultDetailsUpdateHandler,
    DefaultEmailUpdateHandler,
    DefaultPasswordUpdateHandler,
    DefaultSettingsUpdateHandler,
)


def details_update_factory():
    validators = list(
        chain.from_iterable(pluggy.hook.flaskbb_gather_details_update_validators(app=current_app))
    )
    return DefaultDetailsUpdateHandler(db, pluggy, validators)


def password_update_handler():
    validators = list(
        chain.from_iterable(pluggy.hook.flaskbb_gather_password_validators(app=current_app))
    )

    return DefaultPasswordUpdateHandler(db, pluggy, validators)


def email_update_handler():
    validators = list(
        chain.from_iterable(pluggy.hook.flaskbb_gather_email_validators(app=current_app))
    )

    return DefaultEmailUpdateHandler(db, pluggy, validators)


def avatar_update_handler():
    validators = list(
        chain.from_iterable(pluggy.hook.flaskbb_gather_avatar_validators(app=current_app))
    )
    return DefaultAvatarUpdateHandler(db, pluggy, validators)


def settings_update_handler():
    return DefaultSettingsUpdateHandler(db, pluggy)


def settings_form_factory():
    form = GeneralSettingsForm()
    form.theme.choices = get_available_themes()
    form.theme.choices.insert(0, ("", "Default"))
    form.language.choices = get_available_languages()

    if not form.is_submitted() or not form.validate_on_submit():
        form.theme.data = current_user.theme
        form.language.data = current_user.language
        form.open_links_in_new_tab.data = {True: "yes", False: "no"}.get(
            current_user.open_links_in_new_tab, "inherit"
        )

    return form


def change_password_form_factory():
    return ChangePasswordForm(user=current_user)


def change_email_form_factory():
    return ChangeEmailForm(user=current_user)


def change_avatar_form_factory():
    return ChangeAvatarForm(obj=current_user)


def change_details_form_factory():
    return ChangeUserDetailsForm(obj=current_user)
