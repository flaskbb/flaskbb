import pytest
from werkzeug.exceptions import NotFound

from flaskbb.core.settings import flaskbb_config
from flaskbb.forum import views


def test_memberlist_is_reachable_when_enabled(application, default_settings, user):
    view = views.MemberList.as_view("memberlist")

    with application.test_request_context():
        assert user.username in view()


def test_memberlist_returns_404_when_disabled(application, default_settings, user):
    view = views.MemberList.as_view("memberlist")
    flaskbb_config["MEMBERLIST_ENABLED"] = False

    try:
        with application.test_request_context():
            with pytest.raises(NotFound):
                view()
    finally:
        flaskbb_config["MEMBERLIST_ENABLED"] = True
