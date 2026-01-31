# -*- coding: utf-8 -*-
"""
flaskbb.management.models
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains all management related models.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
from typing import override

from sqlalchemy import Enum, ForeignKey, PickleType, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flaskbb.extensions import cache, db
from flaskbb.utils.database import CRUDMixin
from flaskbb.utils.forms import SettingValueType, generate_settings_form
from flaskbb.utils.queries import first_or_404

logger = logging.getLogger(__name__)


class SettingsGroup(db.Model, CRUDMixin):
    __tablename__ = "settingsgroup"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text(), nullable=False)
    settings: Mapped[list["Setting"]] = relationship(
        lazy="dynamic", backref="group", cascade="all, delete-orphan"
    )

    @override
    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.key)


class Setting(db.Model, CRUDMixin):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[PickleType] = mapped_column(PickleType, nullable=False)
    settingsgroup: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("settingsgroup.key", ondelete="CASCADE"),
        nullable=False,
    )

    # The name (displayed in the form)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # The description (displayed in the form)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Available types: string, integer, float, boolean, select, selectmultiple
    value_type: Mapped[SettingValueType] = mapped_column(
        Enum(SettingValueType), nullable=False
    )

    # Extra attributes like, validation things (min, max length...)
    # For Select*Fields required: choices
    extra: Mapped[PickleType] = mapped_column(PickleType)

    @classmethod
    def get_form(cls, group: SettingsGroup):
        """Returns a Form for all settings found in :class:`SettingsGroup`.

        :param group: The settingsgroup name. It is used to get the settings
                      which are in the specified group.
        """
        return generate_settings_form(settings=group.settings)

    @classmethod
    def get_all(cls) -> list["Setting"]:
        return cls.query.all()

    @classmethod
    def update(cls, settings):
        """Updates the cache and stores the changes in the
        database.

        :param settings: A dictionary with setting items.
        """
        # update the database
        for key, value in settings.items():
            setting = db.session.execute(
                db.select(cls).where(Setting.key == key.lower())
            ).scalar()

            setting.value = value

            db.session.add(setting)
            db.session.commit()

        cls.invalidate_cache()

    @classmethod
    def get_settings(cls, from_group=None) -> dict[str, PickleType]:
        """This will return all settings with the key as the key for the dict
        and the values are packed again in a dict which contains
        the remaining attributes.

        :param from_group: Optionally - Returns only the settings from a group.
        """
        result = None
        if from_group is not None:
            result = from_group.settings
        else:
            result = cls.query.all()

        settings = {}
        for setting in result:
            settings[setting.key] = setting.value

        return settings

    @classmethod
    @cache.cached(key_prefix="settings")
    def as_dict(cls, from_group=None, upper=True):
        """Returns all settings as a dict. This method is cached. If you want
        to invalidate the cache, simply execute ``self.invalidate_cache()``.

        :param from_group: Returns only the settings from the group as a dict.
        :param upper: If upper is ``True``, the key will use upper-case
                      letters. Defaults to ``False``.
        """

        settings = {}
        result = None
        if from_group is not None:
            result = first_or_404(
                db.select(SettingsGroup).where(SettingsGroup.key == from_group)
            )
            result = result.settings
        else:
            result = cls.query.all()

        for setting in result:
            if upper:
                setting_key = setting.key.upper()
            else:
                setting_key = setting.key

            settings[setting_key] = setting.value

        return settings

    @classmethod
    def invalidate_cache(cls):
        """Invalidates this objects cached metadata."""
        cache.delete_memoized(cls.as_dict, cls)
