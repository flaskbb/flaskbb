"""
flaskbb.user.plugins
~~~~~~~~~~~~~~~~~~~~

Plugin implementations for the FlaskBB user module.

:copyright: (c) 2018 the FlaskBB Team
:license: BSD, see LICENSE for details
"""

from collections.abc import Generator, Iterable
from itertools import chain
from typing import Any

from flask_allows2 import Permission
from flask_babelplus import gettext as _
from pluggy import HookimplMarker, Result

from ..display.navigation import NavigationDivider, NavigationItem, NavigationLink
from ..settings import flaskbb_config
from ..utils.requirements import IsAtleastModerator
from .models import Guest, User
from .services.validators import (
    CantShareEmailValidator,
    EmailsMustBeDifferent,
    OldEmailMustMatch,
    OldPasswordMustMatch,
    PasswordsMustBeDifferent,
    ValidateAvatarImage,
)

impl = HookimplMarker("flaskbb")


@impl(hookwrapper=True, tryfirst=True)
def flaskbb_tpl_profile_settings_menu() -> Generator[None, Result[Iterable[Any]], None]:
    """
    Flattens the lists that come back from the hook
    into a single iterable that can be used to populate
    the menu
    """
    results = [
        (None, "Account Settings"),
        ("user.settings", "Display"),
        ("user.change_user_details", "User Details"),
        ("user.change_avatar", "Avatar"),
        ("user.change_email", "E-Mail Address"),
        ("user.change_password", "Password"),
    ]
    outcome = yield
    outcome.force_result(chain(results, *outcome.get_result()))


@impl(hookwrapper=True, tryfirst=True)
def flaskbb_tpl_profile_links(user: User) -> Generator[None, Result[Iterable[Any]], None]:
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


def _user_nav_menu(user: User | Guest) -> list[NavigationItem]:
    items: list[NavigationItem] = [
        NavigationLink(
            endpoint="forum.topictracker",
            name=_("Topic Tracker"),
            icon="fa fa-book fa-fw",
        ),
        NavigationDivider(),
        NavigationLink(endpoint="user.settings", name=_("Settings"), icon="fa fa-cog fa-fw"),
    ]

    if Permission(IsAtleastModerator, identity=user):
        items.append(
            NavigationLink(
                endpoint="management.overview",
                name=_("Management"),
                icon="fa fa-lock fa-fw",
            )
        )

    return items


def _guest_nav_menu() -> list[NavigationItem]:
    items: list[NavigationItem] = []

    if flaskbb_config["REGISTRATION_ENABLED"]:
        items.append(
            NavigationLink(
                endpoint="auth.register",
                name=_("Register"),
                icon="fas fa-user-plus fa-fw",
            )
        )

    items.append(
        NavigationLink(
            endpoint="auth.forgot_password",
            name=_("Reset Password"),
            icon="fas fa-undo fa-fw",
        )
    )

    if flaskbb_config["ACTIVATE_ACCOUNT"]:
        items.append(
            NavigationLink(
                endpoint="auth.request_activation_token",
                name=_("Activate Account"),
                icon="fas fa-user-check fa-fw",
            )
        )

    return items


@impl(hookwrapper=True, tryfirst=True)
def flaskbb_tpl_user_nav_menu(
    user: User | Guest,
) -> Generator[None, Result[Iterable[Any]], None]:
    """
    Flattens the lists that come back from the hook into a single iterable
    and keeps the logout link at the end of the menu.
    """
    outcome = yield
    plugin_items = chain(*outcome.get_result())

    if user.is_authenticated:
        logout = [
            NavigationDivider(),
            NavigationLink(endpoint="auth.logout", name=_("Logout"), icon="fa fa-power-off fa-fw"),
        ]
        outcome.force_result(chain(_user_nav_menu(user), plugin_items, logout))
    else:
        outcome.force_result(chain(_guest_nav_menu(), plugin_items))


@impl
def flaskbb_gather_password_validators():
    return [OldPasswordMustMatch(), PasswordsMustBeDifferent()]


@impl
def flaskbb_gather_email_validators():
    return [OldEmailMustMatch(), EmailsMustBeDifferent(), CantShareEmailValidator(User)]


@impl
def flaskbb_gather_avatar_validators():
    return [ValidateAvatarImage()]
