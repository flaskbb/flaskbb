from contextlib import contextmanager

from flask_login import login_user
from flaskbb.extensions import db
from flaskbb.forum import views
from flaskbb.forum.forms import UserSearchForm
from flaskbb.management import views as management_views
from werkzeug.datastructures import MultiDict


def _all(stmt):
    return db.session.scalars(stmt).unique().all()


def test_user_search_form_get_results(request_context, topic):
    user = topic.user
    form = UserSearchForm(
        formdata=MultiDict({"search_query": user.username}),
        meta={"csrf": False},
    )
    assert form.validate()
    assert user in _all(form.get_results())


def test_user_search_form_does_not_match_email(request_context, user):
    form = UserSearchForm(
        formdata=MultiDict({"search_query": user.email}),
        meta={"csrf": False},
    )
    assert form.validate()
    assert _all(form.get_results()) == []


@contextmanager
def _csrf_disabled(application):
    """Search views build their form from `request.form` via
    `self.form()`, so exercising `.post()` end-to-end needs a real form
    submission - which would otherwise be rejected by Flask-WTF's CSRF
    check. Nothing else in this suite posts a FlaskForm through a view,
    so there's no existing helper for this; scope the override to a
    single test via try/finally rather than mutating shared config.
    """
    original = application.config["WTF_CSRF_ENABLED"]
    application.config["WTF_CSRF_ENABLED"] = False
    try:
        yield
    finally:
        application.config["WTF_CSRF_ENABLED"] = original


def test_memberlist_search_finds_user(application, topic):
    user = topic.user
    view = views.MemberList.as_view("memberlist")

    with _csrf_disabled(application):
        with application.test_request_context(
            method="POST", data={"search_query": user.username, "submit": "Search"}
        ):
            resp = view()
            assert user.username in resp


def test_banned_users_search_is_not_filtered_by_ban_status(application, admin_user, user):
    """Documents an existing quirk (not a fix): BannedUsers' search
    path reuses UserSearchForm.get_results() directly and does not
    additionally filter by Group.banned, unlike its own non-search
    listing. `user` (a normal, non-banned member) is still returned by
    a search hit on this page.
    """
    view = management_views.BannedUsers.as_view("banned_users")

    with _csrf_disabled(application):
        with application.test_request_context(
            method="POST", data={"search_query": user.username, "submit": "Search"}
        ):
            login_user(admin_user)
            resp = view()
            assert user.username in resp
