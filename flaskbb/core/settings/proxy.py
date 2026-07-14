# -*- coding: utf-8 -*-
"""
flaskbb.core.settings.proxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the proxy for the settings.

Supports both:
    flaskbb_config.USERS_PER_PAGE      # attribute access, autocompletes
    flaskbb_config['USERS_PER_PAGE']   # dict access, back-compat with existing
                                       # plugin/template code

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from typing import Any

from .models import Setting


class TypedSettingsProxy:
    def __getattr__(self, key: str):
        # only invoked when normal attribute lookup fails
        try:
            return Setting.as_dict()[key.upper()]
        except KeyError:
            raise AttributeError(f"No such setting: {key!r}")

    def __getitem__(self, key: str):
        try:
            return Setting.as_dict()[key.upper()]
        except KeyError:
            raise KeyError(f"No such setting: {key!r}")

    def get(self, key: str, default: Any | None = None):
        return Setting.as_dict().get(key.upper(), default)


flaskbb_config = TypedSettingsProxy()
