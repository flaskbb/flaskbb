from flask import get_flashed_messages
from flask_login import login_user, logout_user
from flaskbb.user import views


def test_delete_avatar_redirects_back_with_a_message(
    application, default_settings, user, monkeypatch
):
    deleted = []
    monkeypatch.setattr(views, "delete_avatar_file", deleted.append)
    user.avatar = "avatar.png"
    user.save()

    with application.test_request_context(method="POST"):
        login_user(user)
        response = views.DeleteAvatar.as_view("delete_avatar")()
        messages = get_flashed_messages(with_categories=True)
        logout_user()

    assert response.status_code == 302
    assert deleted == ["avatar.png"]
    assert user.avatar is None
    assert ("success", "Avatar deleted.") in messages
