from flask import current_app
from flaskbb.extensions import mail
from flaskbb.email import send_reset_token, send_activation_token


def test_send_reset_token_to_user(default_settings, user):
    """ Deliver a contact email. """

    with current_app.test_request_context():
        with mail.record_messages() as outbox:
            send_reset_token(user.id, user.username, user.email)

            assert len(outbox) == 1
            # from /auth/reset-password/<token>
            assert "/auth/reset-password" in outbox[0].body
            assert "/auth/reset-password" in outbox[0].html


def test_send_activation_token_to_user(default_settings, user):
    """ Deliver a contact email. """

    with current_app.test_request_context():
        with mail.record_messages() as outbox:
            send_activation_token(user.id, user.username, user.email)

            assert len(outbox) == 1
            # from /auth/activate/<token>
            assert "/auth/activate" in outbox[0].body
            assert "/auth/activate" in outbox[0].html
