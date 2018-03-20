from datetime import datetime

from pytz import UTC

from ..core.user.repo import UserRepository as BaseUserRepository
from .models import User


class UserRepository(BaseUserRepository):

    def __init__(self, db):
        self.db = db

    def add(self, user_info):
        user = User(
            username=user_info.username,
            email=user_info.email,
            password=user_info.password,
            language=user_info.language,
            primary_group_id=user_info.group,
            date_joined=datetime.now(UTC)
        )
        self.db.session.add(user)

    def get(self, user_id):
        return User.query.get(user_id)

    def find_by(self, **kwargs):
        return User.query.filter_by(**kwargs).all()

    def find_one_by(self, **kwargs):
        return User.query.filter_by(**kwargs).first()
