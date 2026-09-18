import types

import pytest
from flaskbb.display.navigation import NavigationLink
from flaskbb.extensions import pluggy
from flaskbb.management.navigation import ANCHOR, get_management_navigation
from pluggy import HookimplMarker

impl = HookimplMarker("flaskbb")


@pytest.fixture
def menu_plugin():
    module = types.ModuleType("menu_plugin")

    @impl
    def flaskbb_tpl_admin_settings_menu(user):
        return [
            NavigationLink(endpoint="management.plugins", name="Link", icon="fa fa-link"),
            ("management.overview", "Tuple", "fa fa-list"),
        ]

    module.flaskbb_tpl_admin_settings_menu = flaskbb_tpl_admin_settings_menu
    pluggy.register(module, "menu_plugin")

    yield module

    pluggy.unregister(module)


def test_plugin_menu_accepts_links_and_tuples(application, admin_user, menu_plugin):
    with application.test_request_context("/management/plugins"):
        nav = get_management_navigation(admin_user, active_override="management.plugins")

    links = {
        item.name: item
        for item in nav
        if isinstance(item, NavigationLink) and item.name in ("Link", "Tuple")
    }

    assert links["Link"].active
    assert links["Link"].urlforkwargs == {"_anchor": ANCHOR}
    assert not links["Tuple"].active
    assert links["Tuple"].icon == "fa fa-list"
