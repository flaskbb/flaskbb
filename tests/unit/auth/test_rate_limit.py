from datetime import timedelta
from types import SimpleNamespace

import pytest
from flask_limiter import RateLimitExceeded
from flaskbb.auth.forms import LoginForm
from flaskbb.auth.views import Login, login_rate_limit, login_rate_limit_message
from flaskbb.core.settings import flaskbb_config
from flaskbb.extensions import limiter
from flaskbb.utils.helpers import enforce_recaptcha, time_utcnow

pytestmark = pytest.mark.usefixtures("default_settings")


@pytest.fixture()
def clean_limiter(application, monkeypatch):
    """Rate limits live in the in-memory storage of the (package scoped)
    application, so reset them around every test that actually hits one."""
    monkeypatch.setitem(application.config, "WTF_CSRF_ENABLED", False)
    limiter.reset()
    yield limiter
    limiter.reset()


def test_login_rate_limit_uses_the_configured_settings(request_context):
    flaskbb_config.update({"AUTH_REQUESTS": 3, "AUTH_TIMEOUT": 5})

    assert login_rate_limit() == "3/5minutes"


def test_login_rate_limit_message_without_a_current_limit(request_context):
    """Without a current limit there is no reset time to report, so the
    configured window size is used instead of blowing up."""
    flaskbb_config["AUTH_TIMEOUT"] = 15

    assert limiter.current_limit is None
    assert login_rate_limit_message() == "15 minutes"


def test_login_rate_limit_message_uses_the_current_limits_reset_time(
    request_context, monkeypatch
):
    flaskbb_config["AUTH_TIMEOUT"] = 15
    reset_at = int((time_utcnow() + timedelta(minutes=5, seconds=1)).timestamp())
    monkeypatch.setattr(
        type(limiter),
        "current_limit",
        property(lambda self: SimpleNamespace(reset_at=reset_at)),
    )

    # the reset time wins over the configured AUTH_TIMEOUT
    assert login_rate_limit_message() == "5 minutes"


def test_rate_limit_exceeded_gets_a_timeout_description(application, request_context):
    """flask_limiter builds the error description by calling our error_message
    callable from RateLimitExceeded.__init__ - it must not raise."""
    flaskbb_config.update({"AUTH_REQUESTS": 20, "AUTH_TIMEOUT": 15})
    limit = limiter.limit_manager.blueprint_limits(application, "auth")[0]

    assert limit.error_message is login_rate_limit_message

    error = RateLimitExceeded(limit)

    assert error.code == 429
    assert error.description == "15 minutes"


def test_rate_limited_login_returns_429_with_a_timeout(application, clean_limiter):
    flaskbb_config.update({"AUTH_REQUESTS": 2, "AUTH_TIMEOUT": 15})
    credentials = {"login": "nobody", "password": "nothing"}

    with application.test_client() as client:
        for _ in range(flaskbb_config["AUTH_REQUESTS"]):
            assert client.post("/auth/login", data=credentials).status_code != 429

        response = client.post("/auth/login", data=credentials)

    assert response.status_code == 429
    # rendered by the 429 handler from RateLimitExceeded.description
    assert "15 minutes" in response.get_data(as_text=True)


def test_enforce_recaptcha_without_a_current_limit(request_context):
    flaskbb_config["LOGIN_RECAPTCHA"] = 1

    assert limiter.current_limit is None
    assert enforce_recaptcha(limiter) is False


@pytest.mark.parametrize(
    "remaining, expected", [(20, False), (18, False), (17, True), (0, True)]
)
def test_enforce_recaptcha_counts_the_requests_in_the_current_window(
    request_context, monkeypatch, remaining, expected
):
    flaskbb_config.update({"AUTH_REQUESTS": 20, "LOGIN_RECAPTCHA": 3})
    monkeypatch.setattr(
        type(limiter),
        "current_limit",
        property(lambda self: SimpleNamespace(remaining=remaining)),
    )

    assert enforce_recaptcha(limiter) is expected


def test_enforce_recaptcha_after_repeated_logins(
    application, clean_limiter, monkeypatch
):
    """``RequestLimit.remaining`` is already decremented for the request being
    handled, so the captcha kicks in on the LOGIN_RECAPTCHA'th request."""
    flaskbb_config.update(
        {"AUTH_REQUESTS": 10, "AUTH_TIMEOUT": 15, "LOGIN_RECAPTCHA": 3}
    )
    credentials = {"login": "nobody", "password": "nothing"}
    observed = []

    def form(self):
        observed.append(enforce_recaptcha(limiter))
        return LoginForm()

    monkeypatch.setattr(Login, "form", form)

    with application.test_client() as client:
        for _ in range(5):
            client.post("/auth/login", data=credentials)

    assert observed == [False, False, True, True, True]
