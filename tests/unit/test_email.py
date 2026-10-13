from flask import current_app
from flaskbb.email import delay_or_run, send_activation_token, send_reset_token
from flaskbb.extensions import mail
from kombu.exceptions import OperationalError


def test_send_reset_token_to_user(default_settings, user):
    """Deliver a contact email."""

    with current_app.test_request_context():
        with mail.record_messages() as outbox:
            send_reset_token(user.id, user.username, user.email)

            assert len(outbox) == 1
            # from /auth/reset-password/<token>
            assert "/auth/reset-password" in outbox[0].body
            assert "/auth/reset-password" in outbox[0].html


def test_send_activation_token_to_user(default_settings, user):
    """Deliver a contact email."""

    with current_app.test_request_context():
        with mail.record_messages() as outbox:
            send_activation_token(user.id, user.username, user.email)

            assert len(outbox) == 1
            # from /auth/activate/<token>
            assert "/auth/activate" in outbox[0].body
            assert "/auth/activate" in outbox[0].html


def test_email_tasks_ignore_results():
    assert send_activation_token.ignore_result
    assert send_reset_token.ignore_result


def test_delay_or_run_sends_in_process_without_broker(default_settings, mocker):
    mocker.patch.object(send_activation_token, "delay", side_effect=OperationalError)

    with current_app.test_request_context():
        with mail.record_messages() as outbox:
            delay_or_run(send_activation_token, token="token", username="user", email="a@b.c")

            assert len(outbox) == 1
            assert outbox[0].recipients == ["a@b.c"]


def test_delay_or_run_logs_failed_send_without_broker(default_settings, mocker, caplog):
    mocker.patch.object(send_activation_token, "delay", side_effect=OperationalError)
    mocker.patch.object(mail, "send", side_effect=ConnectionRefusedError)

    with current_app.test_request_context():
        delay_or_run(send_activation_token, token="token", username="user", email="a@b.c")

    assert "failed" in caplog.text
