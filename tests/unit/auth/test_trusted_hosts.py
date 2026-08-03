import pytest

from flaskbb.extensions import db

pytestmark = pytest.mark.usefixtures("default_settings")


def test_forgot_password_rejects_untrusted_host_header(application):
    application.config["TRUSTED_HOSTS"] = ["forums.example.org"]
    client = application.test_client()

    # a prior test in this package-scoped app may have left dirty ORM
    # state; flush it before this request's teardown tries to commit it.
    db.session.rollback()

    try:
        response = client.post(
            "/auth/reset-password", headers={"Host": "evil.com"}
        )
        assert response.status_code == 400
    finally:
        application.config["TRUSTED_HOSTS"] = None
