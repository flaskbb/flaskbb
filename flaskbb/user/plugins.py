# -*- coding: utf-8 -*-
"""
    flaskbb.user.plugins
    ~~~~~~~~~~~~~~~~~~~~

    Plugin implementations for the FlaskBB user module.

    :copyright: (c) 2018 the FlaskBB Team
    :license: BSD, see LICENSE for details
"""

from itertools import chain

from flask_babelplus import gettext as _
from pluggy import HookimplMarker

from ..display.navigation import NavigationLink
from .models import User
from .services.validators import (
    CantShareEmailValidator,
    EmailsMustBeDifferent,
    OldEmailMustMatch,
    OldPasswordMustMatch,
    PasswordsMustBeDifferent,
    ValidateAvatarURL,
)

impl = HookimplMarker("flaskbb")


@impl(hookwrapper=True, tryfirst=True)
def flaskbb_tpl_profile_settings_menu():
    """
    Flattens the lists that come back from the hook
    into a single iterable that can be used to populate
    the menu
    """
    results = [
        (None, "Account Settings"),
        ("user.settings", "General Settings"),
        ("user.change_user_details", "Change User Details"),
        ("user.change_email", "Change E-Mail Address"),
        ("user.change_password", "Change Password"),
    ]
    outcome = yield
    outcome.force_result(chain(results, *outcome.get_result()))


@impl(hookwrapper=True, tryfirst=True)
def flaskbb_tpl_profile_sidebar_links(user):
    results = [
        NavigationLink(
            endpoint="user.profile",
            name=_("Overview"),
            icon="fa fa-home",
            urlforkwargs={"username": user.username},
        ),
        NavigationLink(
            endpoint="user.view_all_topics",
            name=_("Topics"),
            icon="fa fa-comments",
            urlforkwargs={"username": user.username},
        ),
        NavigationLink(
            endpoint="user.view_all_posts",
            name=_("Posts"),
            icon="fa fa-comment",
            urlforkwargs={"username": user.username},
        ),
    ]
    outcome = yield
    outcome.force_result(chain(results, *outcome.get_result()))


@impl
def flaskbb_gather_password_validators():
    return [OldPasswordMustMatch(), PasswordsMustBeDifferent()]


@impl
def flaskbb_gather_email_validators():
    return [OldEmailMustMatch(), EmailsMustBeDifferent(), CantShareEmailValidator(User)]


@impl
def flaskbb_gather_details_update_validators():
    return [ValidateAvatarURL()]
