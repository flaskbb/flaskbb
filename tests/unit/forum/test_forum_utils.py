from flask import _request_ctx_stack, url_for

from flaskbb.forum import utils
from flaskbb.forum.models import Forum
from flaskbb.user.models import Group


class TestForceLoginHelpers(object):
    def test_would_not_force_login_for_authed_user(self, user, forum):
        assert not utils.should_force_login(user, forum)

    def test_would_not_force_login_for_anon_in_guest_allowed(self, forum, guest):
        assert not utils.should_force_login(guest, forum)

    def test_would_force_login_for_anon_in_guest_unallowed(self, guest, category):
        forum = Forum(title="no guest", category=category)
        forum.groups = Group.query.filter(Group.guest == False).all()

        assert utils.should_force_login(guest, forum)

    def test_redirects_to_login_with_anon(
        self, guest, category, request_context, application
    ):
        forum = Forum(title="no guest", category=category)
        forum.groups = Group.query.filter(Group.guest == False).all()
        # sets current_forum
        _request_ctx_stack.top.forum = forum

        result = utils.force_login_if_needed()

        # use in rather than == because it can contain query params as well
        assert url_for(application.config["LOGIN_VIEW"]) in result.headers["Location"]
