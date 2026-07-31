from itertools import chain

from pluggy import HookimplMarker

impl = HookimplMarker("flaskbb")


@impl(hookwrapper=True, tryfirst=True)
def flaskbb_tpl_admin_settings_menu(user):
    """
    Flattens the lists that come back from the hook
    into a single iterable that can be used to populate
    the menu. Core items are built separately in
    flaskbb.management.navigation.get_management_navigation.
    """
    outcome = yield
    outcome.force_result(chain(*outcome.get_result()))


@impl(hookwrapper=True, tryfirst=True)
def flaskbb_tpl_admin_settings_sidebar():
    """
    Flattens the lists that come back from the hook
    into a single iterable that can be used to populate
    the menu
    """
    outcome = yield
    outcome.force_result(chain(*outcome.get_result()))
