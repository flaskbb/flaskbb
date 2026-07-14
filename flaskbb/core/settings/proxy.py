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

import logging
from collections.abc import Iterator, MutableMapping
from typing import Any, override

from .models import Setting

logger = logging.getLogger(__name__)


class FlaskBBConfigProxy(MutableMapping[str, Any]):
    def __getattr__(self, key: str):
        # only invoked when normal attribute lookup fails
        try:
            return Setting.as_dict()[key.upper()]
        except KeyError:
            raise AttributeError(f"No such setting: {key!r}")

    @override
    def __getitem__(self, key: str):
        try:
            return Setting.as_dict()[key.upper()]
        except KeyError:
            logger.warning(f"No such setting: {key!r}")
            return None

    @override
    def __setitem__(self, key: str, value: Any) -> None:
        Setting.update({key.lower(): value})

    @override
    def __delitem__(self, key: str) -> None:
        raise NotImplementedError(
            "Settings can't be deleted individually - they're tied to "
            "their group's lifecycle. Use Setting.remove_group(group_key) "
            "to remove an entire group's settings (e.g. on plugin "
            "uninstall)."
        )

    @override
    def __iter__(self) -> Iterator[str]:
        return iter(Setting.as_dict())

    @override
    def __len__(self) -> int:
        return len(Setting.as_dict())

    @override
    def get(self, key: str, default: Any | None = None):
        return Setting.as_dict().get(key, default)


flaskbb_config = FlaskBBConfigProxy()
