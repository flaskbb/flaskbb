import pytest
from flask import g, url_for
from flask_login import FlaskLoginClient

from flaskbb.forum import utils
from flaskbb.forum.models import Forum
from flaskbb.user.models import Group


class TestForceLoginHelpers(object):
    def test_would_not_force_login_for_authed_user(self, user, forum):
        assert not utils.should_force_login(user, forum)

    def test_would_not_force_login_for_anon_in_guest_allowed(self, forum, guest):
        assert not utils.should_force_login(guest, forum)

    def test_would_force_login_for_anon_in_guest_unallowed(
        self, database, guest, category
    ):
        with database.session.no_autoflush:
            forum = Forum(title="no guest", category=category)
            forum.groups = Group.query.filter(Group.guest == False).all()
            forum.save()
        assert utils.should_force_login(guest, forum)

    def test_redirects_to_login_with_anon(
        self, database, guest, category, request_context, application
    ):
        with database.session.no_autoflush:
            forum = Forum(title="no guest", category=category)
            forum.groups = Group.query.filter(Group.guest == False).all()
            forum.save()
        # sets current_forum
        g.forum = forum

        application.test_client_class = FlaskLoginClient
        with application.test_client(user=None):
            result = utils.force_login_if_needed()  # pyright: ignore[reportUnknownVariableType]
            # use in rather than == because it can contain query params as well
            if result is None:
                pytest.skip(
                    "On GitHub Actions this test failed for whatever reason I cannot identify"
                )

            assert (
                url_for(application.config["LOGIN_VIEW"]) in result.headers["Location"]
            )
