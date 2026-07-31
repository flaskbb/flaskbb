"""
flaskbb.management.navigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds the navigation shown in the management panel sidebar.

:copyright: (c) 2018 the FlaskBB Team
:license: BSD, see LICENSE for more details
"""

from flask import request
from flask_allows2 import Permission
from flask_babelplus import gettext as _

from flaskbb.core.settings.registry import setting_registry
from flaskbb.display.navigation import NavigationHeader, NavigationLink, NavigationTree
from flaskbb.extensions import pluggy
from flaskbb.plugins.models import PluginRegistry
from flaskbb.utils.requirements import IsAdmin

ANCHOR = "management-content"


def _settings_tree(user):
    on_settings = request.endpoint == "management.settings"
    slug = request.view_args.get("slug") if on_settings else None
    plugin = request.view_args.get("plugin") if on_settings else None
    active_slug = (slug or "general") if on_settings and plugin is None else None

    children = [
        NavigationLink(
            endpoint="management.settings",
            name=group.name,
            active=group.key == active_slug,
            urlforkwargs={"slug": group.key, "_anchor": ANCHOR},
        )
        for group in setting_registry.core_groups()
    ]

    all_plugins = PluginRegistry.get_installed_plugins()
    extra_links = list(pluggy.hook.flaskbb_tpl_admin_settings_sidebar(user=user))
    if all_plugins or extra_links:
        children.append(NavigationHeader(text=_("Plugin settings"), icon="fa fa-plug"))
        children.extend(
            NavigationLink(
                endpoint="management.settings",
                name=p.name.title(),
                active=p.name == plugin,
                urlforkwargs={"plugin": p.name, "_anchor": ANCHOR},
            )
            for p in all_plugins
        )
        children.extend(extra_links)

    return NavigationTree(
        endpoint="management.settings",
        name=_("Settings"),
        icon="fa fa-cogs",
        active=on_settings,
        urlforkwargs={"_anchor": ANCHOR},
        children=tuple(children),
    )


def _users_tree(user, current_endpoint):
    child_endpoints = ["management.users", "management.banned_users"]

    children = [
        NavigationLink(
            endpoint="management.users",
            name=_("Manage Users"),
            active=current_endpoint == "management.users",
            urlforkwargs={"_anchor": ANCHOR},
        ),
        NavigationLink(
            endpoint="management.banned_users",
            name=_("Banned Users"),
            active=current_endpoint == "management.banned_users",
            urlforkwargs={"_anchor": ANCHOR},
        ),
    ]

    if Permission(IsAdmin, identity=user):
        child_endpoints.append("management.add_user")
        children.append(
            NavigationLink(
                endpoint="management.add_user",
                name=_("Add User"),
                active=current_endpoint == "management.add_user",
                urlforkwargs={"_anchor": ANCHOR},
            )
        )

    return NavigationTree(
        endpoint="management.users",
        name=_("Users"),
        icon="fa fa-user",
        active=current_endpoint in child_endpoints,
        urlforkwargs={"_anchor": ANCHOR},
        children=tuple(children),
    )


def _simple_tree(endpoint, name, icon, current_endpoint, items):
    """Builds a nav item from a static list of (endpoint, label) pairs.

    Returns a plain NavigationLink when there's only one item - a toggle
    with a single child is just a worse link - otherwise a NavigationTree.
    """
    if len(items) == 1:
        item_endpoint, _label = items[0]
        return NavigationLink(
            endpoint=item_endpoint,
            name=name,
            icon=icon,
            active=current_endpoint == item_endpoint,
            urlforkwargs={"_anchor": ANCHOR},
        )

    children = [
        NavigationLink(
            endpoint=item_endpoint,
            name=label,
            active=current_endpoint == item_endpoint,
            urlforkwargs={"_anchor": ANCHOR},
        )
        for item_endpoint, label in items
    ]

    return NavigationTree(
        endpoint=endpoint,
        name=name,
        icon=icon,
        active=current_endpoint in [item_endpoint for item_endpoint, _label in items],
        urlforkwargs={"_anchor": ANCHOR},
        children=tuple(children),
    )


def get_management_navigation(user, active_override=None):
    """Builds the list of NavigationItems shown in the management sidebar.

    :param user: The current user, used to filter admin-only links and to
        query plugin-contributed links.
    :param active_override: Endpoint of the link that should be highlighted
        instead of the one matching the current request. Similar to
        ``{% set active = "management.forums" %}`` in the management pages
        which is used for sub-pages like "add forum".
    """
    current_endpoint = active_override or request.endpoint

    nav = [
        NavigationHeader(text=_("Core"), icon="fa fa-toolbox"),
        NavigationLink(
            endpoint="management.overview",
            name=_("Overview"),
            icon="fa fa-tasks",
            active="management.overview" == current_endpoint,
            urlforkwargs={"_anchor": ANCHOR},
        ),
        _simple_tree(
            "management.unread_reports",
            _("Reports"),
            "fa fa-flag",
            current_endpoint,
            [
                ("management.reports", _("Show all Reports")),
                ("management.unread_reports", _("Show unread Reports")),
            ],
        ),
        _users_tree(user, current_endpoint),
        _simple_tree(
            "management.attachments",
            _("Attachments"),
            "fa fa-paperclip",
            current_endpoint,
            [("management.attachments", _("All Attachments"))],
        ),
    ]

    if Permission(IsAdmin, identity=user):
        nav.extend(
            [
                _simple_tree(
                    "management.groups",
                    _("Groups"),
                    "fa fa-users",
                    current_endpoint,
                    [
                        ("management.groups", _("Manage Groups")),
                        ("management.add_group", _("Add Group")),
                    ],
                ),
                _simple_tree(
                    "management.forums",
                    _("Forums"),
                    "fa fa-comments",
                    current_endpoint,
                    [
                        ("management.forums", _("Manage Forums")),
                        ("management.add_forum", _("Add Forum")),
                        ("management.add_category", _("Add Category")),
                    ],
                ),
                _settings_tree(user),
                NavigationLink(
                    endpoint="management.plugins",
                    name=_("Plugins"),
                    icon="fa fa-puzzle-piece",
                    active="management.plugins" == current_endpoint,
                    urlforkwargs={"_anchor": ANCHOR},
                ),
            ]
        )

    plugin_items = list(pluggy.hook.flaskbb_tpl_admin_settings_menu(user=user))
    if plugin_items:
        nav.append(NavigationHeader(text=_("Plugins"), icon="fa fa-grip"))
        nav.extend(
            NavigationLink(
                endpoint=endpoint,
                name=text,
                icon=icon,
                active=endpoint == current_endpoint,
                urlforkwargs={"_anchor": ANCHOR},
            )
            for endpoint, text, icon in plugin_items
        )

    return nav
