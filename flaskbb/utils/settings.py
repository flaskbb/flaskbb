# -*- coding: utf-8 -*-
"""
flaskbb.utils.settings
~~~~~~~~~~~~~~~~~~~~~~

This module contains the interface for interacting with FlaskBB's
configuration.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
from collections.abc import MutableMapping
from typing import Any, override

from flaskbb.management.models import Setting

logger = logging.getLogger(__name__)


class FlaskBBConfig(MutableMapping[str, Any | None]):
    """Provides a dictionary like interface for interacting with FlaskBB's
    Settings cache.
    """

    def __init__(self, *args, **kwargs):
        self.update(dict(*args, **kwargs))

    @override
    def __getitem__(self, key: str) -> Any:
        try:
            return Setting.as_dict()[key]
        except KeyError:
            logger.info(f"Couldn't find setting for key ${key}")
            return None

    @override
    def __setitem__(self, key: str, value: Any):
        Setting.update({key.lower(): value})

    def __delitem__(self, key: str):  # pragma: no cover
        pass

    def __iter__(self):
        return iter(Setting.as_dict())

    def __len__(self):
        return len(Setting.as_dict())


flaskbb_config = FlaskBBConfig()
