from collections.abc import Generator, Iterable
from itertools import chain
from typing import Any, TYPE_CHECKING

from pluggy import HookimplMarker, Result

if TYPE_CHECKING:
    from flaskbb.user.models import Guest, User

impl = HookimplMarker("flaskbb")


@impl(hookwrapper=True, tryfirst=True)
def flaskbb_tpl_admin_settings_menu(
    user: "User | Guest",
) -> Generator[None, Result[Iterable[Any]], None]:
    """
    Flattens the lists that come back from the hook
    into a single iterable that can be used to populate
    the menu. Core items are built separately in
    flaskbb.management.navigation.get_management_navigation.
    """
    outcome = yield
    outcome.force_result(chain(*outcome.get_result()))


@impl(hookwrapper=True, tryfirst=True)
def flaskbb_tpl_admin_settings_sidebar() -> Generator[None, Result[Iterable[Any]], None]:
    """
    Flattens the lists that come back from the hook
    into a single iterable that can be used to populate
    the menu
    """
    outcome = yield
    outcome.force_result(chain(*outcome.get_result()))
