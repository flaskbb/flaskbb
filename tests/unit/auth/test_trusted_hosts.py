import pytest
from flask import g

pytestmark = pytest.mark.usefixtures("default_settings")


def test_forgot_password_rejects_untrusted_host_header(application):
    application.config["TRUSTED_HOSTS"] = ["forums.example.org"]
    client = application.test_client()

    # the package-scoped app context is never popped between tests.
    g.pop("_login_user", None)

    try:
        response = client.post("/auth/reset-password", headers={"Host": "evil.com"})
        assert response.status_code == 400
    finally:
        application.config["TRUSTED_HOSTS"] = None
