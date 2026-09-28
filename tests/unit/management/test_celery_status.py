from flask_login import login_user, logout_user
from flaskbb.management import views


class _Inspect:
    def __init__(self, reply):
        self.reply = reply

    def ping(self):
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def _status(actor, monkeypatch, reply):
    monkeypatch.setattr(views.celery.control, "inspect", lambda: _Inspect(reply))

    with views.current_app.test_request_context():
        login_user(actor)
        response = views.CeleryStatus.as_view("celery_status")()
        logout_user()

    return response


def test_running_celery_only_updates_the_status(default_settings, moderator_user, monkeypatch):
    response = _status(moderator_user, monkeypatch, {"worker": {"ok": "pong"}})

    assert 'id="celery-status" class="text-success"' in response
    assert "hx-swap-oob" not in response


def test_stopped_celery_takes_the_place_of_the_notice(
    default_settings, moderator_user, monkeypatch
):
    response = _status(moderator_user, monkeypatch, ConnectionError("no broker"))

    assert 'id="celery-status" class="text-danger"' in response
    assert 'id="overview-no-notifications"' in response
    assert 'hx-swap-oob="true"' in response
