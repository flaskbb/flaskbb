from flask_login import login_user, logout_user
from flask_login.test_client import FlaskLoginClient
from sqlalchemy import select

from flaskbb.extensions import db
from flaskbb.forum.models import Topic
from flaskbb.user.models import Guest
from flaskbb.utils.queries import hidden


def test_guest_user_cannot_see_hidden_posts(
    application, guest: Guest, topic, user, request_context
):
    topic.hide(user)

    logout_user()
    application.test_client_class = FlaskLoginClient
    with application.test_client(user=None):
        login_user(guest)

        hidden_topic = db.session.execute(
            hidden(select(Topic).where(Topic.id == topic.id))
        ).scalar()

        assert hidden_topic is None


def test_regular_user_cannot_see_hidden_posts(
    application, topic, user, request_context
):
    topic.hide(user)

    logout_user()
    application.test_client_class = FlaskLoginClient
    with application.test_client(user=user):
        login_user(user)

        assert (
            db.session.execute(
                hidden(select(Topic).where(Topic.id == topic.id))
            ).scalar()
            is None
        )


def test_moderator_user_can_see_hidden_posts(
    application, topic, moderator_user, request_context
):
    topic.hide(moderator_user)

    logout_user()
    application.test_client_class = FlaskLoginClient
    with application.test_client(user=moderator_user):
        login_user(moderator_user)

        assert (
            db.session.execute(
                hidden(select(Topic).where(Topic.id == topic.id))
            ).scalar()
            is not None
        )


def test_super_moderator_user_can_see_hidden_posts(
    application, topic, super_moderator_user, request_context
):
    topic.hide(super_moderator_user)

    logout_user()
    application.test_client_class = FlaskLoginClient
    with application.test_client(user=super_moderator_user):
        login_user(super_moderator_user)
        assert (
            db.session.execute(
                hidden(select(Topic).where(Topic.id == topic.id))
            ).scalar()
            is not None
        )


def test_admin_user_can_see_hidden_posts(
    application, topic, admin_user, request_context
):
    topic.hide(admin_user)

    logout_user()
    application.test_client_class = FlaskLoginClient
    with application.test_client(user=admin_user):
        login_user(admin_user)
        assert (
            db.session.execute(
                hidden(select(Topic).where(Topic.id == topic.id))
            ).scalar()
            is not None
        )
