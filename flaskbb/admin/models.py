import sys
import base64
try:
    import cPickle as pickle
except ImportError:
    import pickle

from flaskbb.extensions import db, cache


def normalize_to(value, value_type, reverse=False):
    """Converts a value to a specified value type.
    Available value types are: string, int, boolean, list.
    A boolean type is handled as 0 for false and 1 for true.
    Raises a exception if the value couldn't be converted

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
    name = db.Column(db.String)
    description = db.Column(db.String)


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String, primary_key=True)
    _value = db.Column("value", db.String)
    group = db.Column(db.String, db.ForeignKey('settingsgroup', use_alter=True,
                                               name="fk_settingsgroup"))

    # The name (displayed in the form)
    name = db.Column(db.String)

    # The description (displayed in the form)
    description = db.Column(db.String)

    # Available types: string, integer, boolean, array, float
    value_type = db.Column(db.String)

    # Available types: text, choice, yesno
    input_type = db.Column(db.String)

    # Extra attributes like, validation things (min, max length...)
    _extra = db.Column("extra", db.String)

    settings_group = db.relationship("SettingsGroup", lazy="dynamic",
                                     backref="setting")

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

    def get_field(self):
        pass

    @classmethod
    @cache.memoize(timeout=sys.maxint)
    def get_all(cls):
        pass

    def save(self):
        db.session.add(self)
        db.session.commit()

    def invalidate_cache(self):
        cache.delete_memoized(self.get_all, self)
