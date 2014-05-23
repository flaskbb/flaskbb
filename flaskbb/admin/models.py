from flask import current_app
from flaskbb.extensions import db


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


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=True)
    value = db.Column(db.String)

    # Available types: string, int, boolean
    value_type = db.Column(db.String)

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def update(cls, configs):
        """Updates the current_app's config and stores the changes in the
        database.

        :param config: A dictionary with configuration items.
        """
        result = []
        updated_configs = {}
        for key, value in configs.iteritems():
            config = cls.query.filter(Settings.key == key.lower()).first()

            value = convert_to(value, config.value_type)
            config.value = value

            updated_configs[config.key.upper()] = config.value
            result.append(config)

            print "{}: {}".format(config.key, config.value)
            db.session.add(config)
            db.session.commit()

        print updated_configs
        current_app.config.update(updated_configs)

    @classmethod
    def get_all(cls):
        """Returns all settings as a dictionary
        The key is the same as in the config files.
        """
        settings = {}
        all_settings = cls.query.all()
        for setting in all_settings:
            settings[setting.key.upper()] = setting.value

        return settings
