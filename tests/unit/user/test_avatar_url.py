import pytest


@pytest.mark.parametrize(
    ("avatar", "avatar_url"),
    [
        ("avatar_test_normal.png", "/uploads/avatar/avatar_test_normal.png"),
        # FlaskBB 2.x avatars link to an external image
        ("https://example.org/test_normal.png", "https://example.org/test_normal.png"),
        ("http://example.org/test_normal.png", "http://example.org/test_normal.png"),
    ],
)
def test_avatar_url(request_context, user, avatar, avatar_url):
    user.avatar = avatar

    assert user.avatar_url == avatar_url
