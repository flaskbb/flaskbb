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
from .registry import setting_registry

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
        # (group_key, key) together identify a setting now, not key
        # alone - resolve_display_key() reverses the GROUPKEY_KEY
        # display form back into the pair Setting.update() needs
        group_key, raw_key = setting_registry.resolve_display_key(key)
        Setting.update(group_key, {raw_key: value})

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
        return Setting.as_dict().get(key.upper(), default)

    @override
    def update(self, other=(), /, **kwargs: dict[str, Any]) -> None:  # pyright: ignore
        """Batches every key/value pair into as few Setting.update()
        calls as possible - one per group involved, each a single
        commit + cache invalidation - instead of the MutableMapping
        mixin's default, which would call __setitem__ (and so resolve +
        Setting.update()) once per key regardless of grouping.

        Accepts the same shapes dict.update() does: a mapping, an
        iterable of (key, value) pairs, keyword arguments, or any
        combination - matching MutableMapping's own update() signature.

        Since (group_key, key) together identify a setting, keys from
        different groups can't be saved in a single Setting.update()
        call - this groups the incoming keys by their resolved
        group_key first, then issues one call per group.
        """
        combined: dict[str, Any] = dict(other)  # pyright: ignore
        combined.update(kwargs)

        by_group: dict[str, dict[str, Any]] = {}
        for display_key, value in combined.items():
            group_key, raw_key = setting_registry.resolve_display_key(display_key)
            by_group.setdefault(group_key, {})[raw_key] = value

        for group_key, form_data in by_group.items():
            Setting.update(group_key, form_data)


flaskbb_config = FlaskBBConfigProxy()
