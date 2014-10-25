# -*- coding: utf-8 -*-
"""
    flaskbb.management.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains all management related models.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
from wtforms import (TextField, IntegerField, FloatField, BooleanField,
                     SelectField, SelectMultipleField, validators)
from flask.ext.wtf import Form
from flaskbb._compat import max_integer, text_type, iteritems
from flaskbb.extensions import db, cache


class SettingsGroup(db.Model):
    __tablename__ = "settingsgroup"

    key = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    settings = db.relationship("Setting", lazy="dynamic", backref="group",
                               cascade="all, delete-orphan")

    def save(self):
        """Saves a settingsgroup."""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Deletes a settingsgroup."""
        db.session.delete(self)
        db.session.commit()


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String(255), primary_key=True)
    value = db.Column(db.PickleType, nullable=False)
    settingsgroup = db.Column(db.String,
                              db.ForeignKey('settingsgroup.key',
                                            use_alter=True,
                                            name="fk_settingsgroup"),
                              nullable=False)

    # The name (displayed in the form)
    name = db.Column(db.String(200), nullable=False)

    # The description (displayed in the form)
    description = db.Column(db.Text, nullable=False)

    # Available types: string, integer, float, boolean, select, selectmultiple
    value_type = db.Column(db.String(20), nullable=False)

    # Extra attributes like, validation things (min, max length...)
    # For Select*Fields required: choices
    extra = db.Column(db.PickleType)

    @classmethod
    def get_form(cls, group):
        """Returns a Form for all settings found in :class:`SettingsGroup`.

        :param group: The settingsgroup name. It is used to get the settings
                      which are in the specified group.
        """

        class SettingsForm(Form):
            pass

        # now parse the settings in this group
        for setting in group.settings:
            field_validators = []

            # generate the validators
            if "min" in setting.extra:
                # Min number validator
                if setting.value_type in ("integer", "float"):
                    field_validators.append(
                        validators.NumberRange(min=setting.extra["min"])
                    )

                # Min text length validator
                elif setting.value_type in ("string"):
                    field_validators.append(
                        validators.Length(min=setting.extra["min"])
                    )

            if "max" in setting.extra:
                # Max number validator
                if setting.value_type in ("integer", "float"):
                    field_validators.append(
                        validators.NumberRange(max=setting.extra["max"])
                    )

                # Max text length validator
                elif setting.value_type in ("string"):
                    field_validators.append(
                        validators.Length(max=setting.extra["max"])
                    )

            # Generate the fields based on value_type
            # IntegerField
            if setting.value_type == "integer":
                setattr(
                    SettingsForm, setting.key,
                    IntegerField(setting.name, validators=field_validators,
                                 description=setting.description)
                )
            # FloatField
            elif setting.value_type == "float":
                setattr(
                    SettingsForm, setting.key,
                    FloatField(setting.name, validators=field_validators,
                               description=setting.description)
                )

            # TextField
            if setting.value_type == "string":
                setattr(
                    SettingsForm, setting.key,
                    TextField(setting.name, validators=field_validators,
                              description=setting.description)
                )

            # SelectMultipleField
            if setting.value_type == "selectmultiple":
                # if no coerce is found, it will fallback to unicode
                if "coerce" in setting.extra:
                    coerce_to = setting.extra['coerce']
                else:
                    coerce_to = text_type

                setattr(
                    SettingsForm, setting.key,
                    SelectMultipleField(
                        setting.name,
                        choices=setting.extra['choices'](),
                        coerce=coerce_to,
                        description=setting.description
                    )
                )

            # SelectField
            if setting.value_type == "select":
                # if no coerce is found, it will fallback to unicode
                if "coerce" in setting.extra:
                    coerce_to = setting.extra['coerce']
                else:
                    coerce_to = text_type

                setattr(
                    SettingsForm, setting.key,
                    SelectField(
                        setting.name,
                        coerce=coerce_to,
                        choices=setting.extra['choices'](),
                        description=setting.description)
                )

            # BooleanField
            if setting.value_type == "boolean":
                setattr(
                    SettingsForm, setting.key,
                    BooleanField(setting.name, description=setting.description)
                )

        return SettingsForm

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def update(cls, settings, app=None):
        """Updates the cache and stores the changes in the
        database.

        :param settings: A dictionary with setting items.
        """
        # update the database
        for key, value in settings.iteritems():
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
            settings[setting.key] = {
                'name': setting.name,
                'description': setting.description,
                'value': setting.value,
                'value_type': setting.value_type,
                'extra': setting.extra
            }

        return settings

    @classmethod
    @cache.memoize(timeout=max_integer)
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
            print(Setting.query)
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

    def save(self):
        """Saves a setting"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Deletes a setting"""
        db.session.delete(self)
        db.session.commit()
