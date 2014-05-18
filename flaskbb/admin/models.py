from flask import current_app
from flaskbb.extensions import db


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String, unique=True)
    value = db.Column(db.String)

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def update(cls):
        current_app.config.update(cls.get_all())

    @classmethod
    def get_all(cls):
        settings = {}
        all_settings = cls.query.all()
        for setting in all_settings:
            settings[setting.key.upper()] = setting.value

        return settings
