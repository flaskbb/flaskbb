from flask import current_app

from ...extensions import db
from .update import TopicUpdateHandler


def topic_factory():
    return TopicUpdateHandler(db, current_app.pluggy)
