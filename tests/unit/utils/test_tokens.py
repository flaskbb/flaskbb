from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer
from flaskbb.utils.tokens import make_token, get_token_status


def test_make_token(user):
    token = make_token(user, "test")
    s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
    unpacked_token = s.loads(token)
    assert user.id == unpacked_token["id"]
    assert "test" == unpacked_token["op"]


def test_valid_token_status(user):
    token = make_token(user, "valid_test")
    expired, invalid, token_user = get_token_status(token, "valid_test")

    assert not expired
    assert not invalid
    assert token_user == user


def test_token_status_with_data(user):
    token = make_token(user, "test_data")
    expired, invalid, token_user, data = \
        get_token_status(token, "test_data", return_data=True)
    assert user.id == data["id"]
    assert "test_data" == data["op"]


def test_token_operation(user):
    token = make_token(user, "operation_test")
    expired, invalid, token_user = get_token_status(token, "invalid_op")
    assert invalid
    assert not expired
    assert not token_user


def test_invalid_token_status(user):
    token = "this-is-not-a-token"
    expired, invalid, token_user, data = \
        get_token_status(token, "invalid_test", return_data=True)

    assert invalid
    assert not expired
    assert not token_user
    assert data is None


def test_expired_token_status(user):
    token = make_token(user, "expired_test", -1)
    expired, invalid, token_user = get_token_status(token, "expired_test")
    assert expired
    assert not invalid
    assert not token_user
