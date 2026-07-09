"""
A proxy for the settings.

Supports both:
    flaskbb_config.USERS_PER_PAGE      # attribute access, autocompletes
    flaskbb_config['USERS_PER_PAGE']   # dict access, back-compat with existing
                                       # plugin/template code
"""

from typing import Any

from .models import Setting


class TypedSettingsProxy:
    def __getattr__(self, key: str):
        # only invoked when normal attribute lookup fails
        try:
            return Setting.as_dict()[key]
        except KeyError:
            raise AttributeError(f"No such setting: {key!r}")

    def __getitem__(self, key: str):
        try:
            return Setting.as_dict()[key]
        except KeyError:
            raise KeyError(f"No such setting: {key!r}")

    def get(self, key: str, default: Any | None = None):
        return Setting.as_dict().get(key, default)


flaskbb_config = TypedSettingsProxy()
