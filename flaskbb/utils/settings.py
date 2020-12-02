# -*- coding: utf-8 -*-
"""
    flaskbb.utils.settings
    ~~~~~~~~~~~~~~~~~~~~~~

    This module contains the interface for interacting with FlaskBB's
    configuration.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from collections.abc import MutableMapping

from flaskbb.management.models import Setting


class FlaskBBConfig(MutableMapping):
    """Provides a dictionary like interface for interacting with FlaskBB's
    Settings cache.
    """

    def __init__(self, *args, **kwargs):
        self.update(dict(*args, **kwargs))

    def __getitem__(self, key):
        return Setting.as_dict()[key]

    def __setitem__(self, key, value):
        Setting.update({key.lower(): value})

    def __delitem__(self, key):  # pragma: no cover
        pass

    def __iter__(self):
        return iter(Setting.as_dict())

    def __len__(self):
        return len(Setting.as_dict())


flaskbb_config = FlaskBBConfig()
