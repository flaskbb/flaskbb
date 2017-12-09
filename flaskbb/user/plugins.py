from itertools import chain
from pluggy import HookimplMarker

impl = HookimplMarker('flaskbb')


@impl(hookwrapper=True, tryfirst=True)
def flaskbb_tpl_profile_settings_menu():
    """
    Flattens the lists that come back from the hook
    into a single iterable that can be used to populate
    the menu
    """
    results = [
        (None, 'Account Settings'),
        ('user.settings', 'General Settings'),
        ('user.change_user_details', 'Change User Details'),
        ('user.change_email', 'Change E-Mail Address'),
        ('user.change_password', 'Change Password')
    ]
    outcome = yield
    outcome.force_result(chain(results, *outcome.get_result()))
