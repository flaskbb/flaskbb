import sys
import base64
try:
    import cPickle as pickle
except ImportError:
    import pickle

from wtforms import (TextField, IntegerField, BooleanField, SelectField,
                     FloatField, validators)
from flask.ext.wtf import Form
from flaskbb.extensions import db, cache


def normalize_to(value, value_type, reverse=False):
    """Converts a value to a specified value type.
    Available value types are: string, integer, boolean and array.
    A boolean type is handled as 0 for false and 1 for true.

    :param value: The value which should be converted.
    :param value_type: The value_type.
    :param reverse: If the value should be converted back
    """
    if reverse:
        if value_type == 'array':
            return value.split(',')
        if value_type == 'integer':
            return int(value)
        if value_type == 'float':
            return float(value)
        if value_type == 'boolean':
            return value == "1"

        # text
        return value
    else:
        if value_type == 'array':
            return ",".join(value)
        if value_type == 'integer':
            return int(value)
        if value_type == 'float':
            return float(value)
        if value_type == 'boolean':
            return 1 if value else 0

        # text
        return value


class SettingsGroup(db.Model):
    __tablename__ = "settingsgroup"

    key = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    settings = db.relationship("Setting", lazy="dynamic", backref="group")

    def save(self):
        db.session.add(self)
        db.session.commit()


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String, primary_key=True)
    _value = db.Column("value", db.String, nullable=False)
    settingsgroup = db.Column(db.String,
                              db.ForeignKey('settingsgroup.key',
                                            use_alter=True,
                                            name="fk_settingsgroup"),
                              nullable=False)

    # The name (displayed in the form)
    name = db.Column(db.String, nullable=False)

    # The description (displayed in the form)
    description = db.Column(db.String, nullable=False)

    # Available types: string, integer, boolean, array, float
    value_type = db.Column(db.String, nullable=False)

    # Available types: text, number, choice, yesno
    # They are used in the form creation process
    input_type = db.Column(db.String, nullable=False)

    # Extra attributes like, validation things (min, max length...)
    _extra = db.Column("extra", db.String)

    # Properties
    @property
    def value(self):
        return normalize_to(self._value, self.value_type)

    @value.setter
    def value(self, value):
        self._value = normalize_to(value, self.value_type, reverse=True)

    @property
    def extra(self):
        return pickle.loads(base64.decodestring(self._extra))

    @extra.setter
    def extra(self, extra):
        self._extra = base64.encodestring(
            pickle.dumps((extra), pickle.HIGHEST_PROTOCOL)
        )

    @classmethod
    @cache.memoize(timeout=sys.maxint)
    def config(self):
        """Returns the configs as a dict (only self.key and self.value).
        If a value/key has changed, you need to invalidate the cache."""
        settings = {}
        for setting in self.get_all():
            settings[setting.key.upper()] = setting.value

        return settings

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def get_form(cls, group):
        """Returns a Form for all settings found in :class:`SettingsGroup`.

        :param group: The settingsgroup name. It is used to get the settings
                      which are in the specified group. Aborts with 404 if the
                      group is found.
        """
        settings = SettingsGroup.query.filter_by(key=group).first_or_404()

        class SettingsForm(Form):
            pass

        # now parse that shit
        for setting in settings.settings:
            field_validators = []

            # generate the validators
            # TODO: Do this in another function
            if "min" in setting.extra:
                # Min number validator
                if setting.value_type in ("integer", "float"):
                    field_validators.append(
                        validators.NumberRange(min=setting.extra["min"])
                    )

                # Min text length validator
                elif setting.value_type in ("string", "array"):
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
                elif setting.value_type in ("string", "array"):
                    field_validators.append(
                        validators.Length(max=setting.extra["max"])
                    )

            # Generate the fields based on input_type and value_type
            if setting.input_type == "number":
                # IntegerField
                if setting.value_type == "integer":
                    setattr(
                        SettingsForm, setting.key,
                        IntegerField(setting.name, field_validators)
                    )
                # FloatField
                elif setting.value_type == "float":
                    setattr(
                        SettingsForm, setting.key,
                        FloatField(setting.name, field_validators)
                    )

            # TextField
            if setting.input_type == "text":
                setattr(
                    SettingsForm, setting.key,
                    TextField(setting.name, field_validators)
                )

            # SelectField
            if setting.input_type == "choice" and "choices" in setting.extra:
                setattr(
                    SettingsForm, setting.key,
                    SelectField(setting.name, choices=setting.extra['choices'])
                )

            # BooleanField
            if setting.input_type == "yesno":
                setattr(
                    SettingsForm, setting.key,
                    BooleanField(setting.name)
                )

        return SettingsForm()

    @classmethod
    def update(self, app):
        """Updates the config for the app

        :param app: The application.
        """
        self.invalidate_cache()

        app.config.update(self.config())

    def save(self):
        db.session.add(self)
        db.session.commit()

    def invalidate_cache(self):
        cache.delete_memoized(self.config, self)
