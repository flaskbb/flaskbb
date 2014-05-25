import sys

from flask import current_app
from flaskbb.extensions import db, cache


def convert_to(value, value_type="text"):
    """Converts a value to a specified value type.
    Available value types are: string, int, boolean, list.
    A boolean type is handled as 0 for false and 1 for true.
    Raises a exception if the value couldn't be converted

    :param value: The value which should be converted.
    :param value_type: The value_type.
    """
    print "converting..."
    if value_type == "text":
        print "text %s" % value
        if isinstance(value, str):
            return value
        else:
            try:
                value = str(value)
            except ValueError:
                raise ValueError("Couldn't convert value to {}"
                                 .format(value_type))
            return value

    elif value_type == "int":
        print "int %s" % value
        try:
            value = int(value)
        except ValueError:
            raise ValueError("Couldn't convert value to {}"
                             .format(value_type))
        print type(value)
        return value

    elif value_type == "boolean":
        try:
            value = int(value)

            if value < 0 or value > 1:
                raise ValueError("Value is not a boolean!. Value must be "
                                 "between 0 and 1.")
            else:
                return value

        except ValueError:
            raise ValueError("Couldn't convert value to {}"
                             .format(value_type))


class SettingsGroup(db.Model):
    __tablename__ = "settingsgroup"

    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.String)
    description = db.Column(db.String)


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.String)
    group = db.Column(db.String, db.ForeignKey('settingsgroup', use_alter=True,
                                               name="fk_settingsgroup"))

    # The name (displayed in the form)
    name = db.Column(db.String)

    # The description (displayed in the form)
    description = db.Column(db.String)

    # Available types: string, int, boolean
    value_type = db.Column(db.String)

    # Available types: text, choice, yesno
    input_type = db.Column(db.String)

    # Extra attributes like, validation things (min, max length...)
    extra = db.Column(db.String)

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    @cache.memoize(timeout=sys.maxint)
    def get_all(cls):
        pass

    def invalidate_cache(self):
        cache.delete_memoized(self.get_all, self)
