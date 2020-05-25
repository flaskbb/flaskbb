# -*- coding: utf-8 -*-
"""
    flaskbb.management.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains all management related models.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging

from flaskbb._compat import iteritems
from flaskbb.extensions import cache, db
from flaskbb.utils.database import CRUDMixin
from flaskbb.utils.forms import SettingValueType, generate_settings_form

logger = logging.getLogger(__name__)


class SettingsGroup(db.Model, CRUDMixin):
    __tablename__ = "settingsgroup"

    key = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    settings = db.relationship("Setting", lazy="dynamic", backref="group",
                               cascade="all, delete-orphan")

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.key)


class Setting(db.Model, CRUDMixin):
    __tablename__ = "settings"

    key = db.Column(db.String(255), primary_key=True)
    value = db.Column(db.PickleType, nullable=False)
    settingsgroup = db.Column(db.String(255),
                              db.ForeignKey('settingsgroup.key',
                                            ondelete="CASCADE"),
                              nullable=False)

    # The name (displayed in the form)
    name = db.Column(db.String(200), nullable=False)

    # The description (displayed in the form)
    description = db.Column(db.Text, nullable=False)

    # Available types: string, integer, float, boolean, select, selectmultiple
    value_type = db.Column(db.Enum(SettingValueType), nullable=False)

    # Extra attributes like, validation things (min, max length...)
    # For Select*Fields required: choices
    extra = db.Column(db.PickleType)

    @classmethod
    def get_form(cls, group):
        """Returns a Form for all settings found in :class:`SettingsGroup`.

        :param group: The settingsgroup name. It is used to get the settings
                      which are in the specified group.
        """
        return generate_settings_form(settings=group.settings)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def update(cls, settings):
        """Updates the cache and stores the changes in the
        database.

        :param settings: A dictionary with setting items.
        """
        # update the database
        for key, value in iteritems(settings):
            setting = cls.query.filter(Setting.key == key.lower()).first()

            setting.value = value

            db.session.add(setting)
            db.session.commit()

        cls.invalidate_cache()

    @classmethod
    def get_settings(cls, from_group=None):
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
            result = SettingsGroup.query.filter_by(key=from_group).\
                first_or_404()
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
