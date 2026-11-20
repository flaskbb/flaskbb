import pytest


@pytest.mark.parametrize("secret", ["", "  ", "secret key", " secret key ", b"secret key"])
def test_insecure_secret_rejects_requests(application, monkeypatch, secret):
    monkeypatch.setitem(application.config, "SECRET_KEY", secret)
    response = application.test_client().get("/auth/login")
    assert response.status_code == 503
