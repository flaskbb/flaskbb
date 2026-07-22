from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from flask_login import login_user
from werkzeug.datastructures import MultiDict

from flaskbb.extensions import cache, db
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.search import service, views
from flaskbb.search.forms import SearchForm


def _all(stmt):
    return db.session.scalars(stmt).unique().all()


def test_search_form_forum_type_defaults_to_topics_only(request_context, topic):
    form = SearchForm(
        formdata=MultiDict(
            {"search_query": "Test Topic Normal", "search_type": "forum"}
        ),
        meta={"csrf": False},
        user=topic.user,
    )
    assert form.validate()

    results = form.get_results()
    assert set(results.keys()) == {"topic"}
    assert topic in _all(results["topic"])


def test_search_form_forum_type_can_be_narrowed_to_posts(request_context, topic):
    form = SearchForm(
        formdata=MultiDict(
            {
                "search_query": "Test Content Normal",
                "search_type": "forum",
                "content_type": "post",
            }
        ),
        meta={"csrf": False},
        user=topic.user,
    )
    assert form.validate()

    results = form.get_results()
    assert set(results.keys()) == {"post"}
    assert topic.first_post in _all(results["post"])


def test_search_form_user_type_returns_users(request_context, topic):
    searched_user = topic.user
    form = SearchForm(
        formdata=MultiDict(
            {"search_query": searched_user.username, "search_type": "user"}
        ),
        meta={"csrf": False},
        user=searched_user,
    )
    assert form.validate()

    results = form.get_results()
    assert set(results.keys()) == {"user"}
    assert searched_user in _all(results["user"])


def test_search_form_forum_choices_are_permission_scoped(
    request_context, forum, user, admin_user, default_groups
):
    # User.get_groups()/.get_permissions() are @cache.memoize()'d by
    # username, and the cache outlives a single test (the app fixture is
    # package-scoped) - clear it so an earlier test's cached result for
    # "test_normal"/"test_admin" can't leak into this assertion.
    cache.clear()

    restricted = Forum(title="Admin Only Forum", category_id=forum.category_id)
    restricted.groups = [default_groups[0]]
    restricted.save(groups=restricted.groups)

    form = SearchForm(meta={"csrf": False}, user=user)
    choices = [f.id for f in form.forum_id.query_factory()]
    assert forum.id in choices
    assert restricted.id not in choices

    admin_form = SearchForm(meta={"csrf": False}, user=admin_user)
    admin_choices = [f.id for f in admin_form.forum_id.query_factory()]
    assert restricted.id in admin_choices


def test_search_forums_excludes_inaccessible_forum_even_if_forced(
    request_context, forum, user, default_groups
):
    """Defense in depth: even if `forum_id` is forced to a forum outside
    the user's groups (e.g. a hand-crafted POST bypassing the dropdown),
    results from that forum must not leak through.
    """
    cache.clear()  # see comment in test_search_form_forum_choices_are_permission_scoped

    restricted = Forum(title="Admin Only Forum", category_id=forum.category_id)
    restricted.groups = [default_groups[0]]
    restricted.save(groups=restricted.groups)

    post = Post(content="Secret Content")
    Topic(title="Secret Topic").save(forum=restricted, user=user, post=post)

    results = service.search_forums("Secret Topic", user, forum=restricted)
    assert _all(results["topic"]) == []


def test_search_forums_filters_by_author(request_context, topic, user, Fred):
    post = Post(content="Test Content Normal")
    Topic(title="Test Topic Normal").save(forum=topic.forum, user=Fred, post=post)

    results = service.search_forums("Test Topic Normal", user, author=Fred.username)

    topics = _all(results["topic"])
    assert topic not in topics
    assert all(t.username == Fred.username for t in topics)


def test_search_forums_filters_by_date_range(request_context, topic, user):
    # Regression: DateField yields a plain `date`, but `date_created` is a
    # tz-aware UTCDateTime column - a bare date used to blow up in binding.
    # `date_to=today` must also include a topic created earlier today.
    today = datetime.now(timezone.utc).date()

    results = service.search_forums(
        "Test Topic Normal",
        user,
        date_from=today - timedelta(days=1),
        date_to=today,
    )

    assert topic in _all(results["topic"])


def test_search_forums_excludes_topics_outside_date_range(
    request_context, topic, user
):
    past = datetime.now(timezone.utc).date() - timedelta(days=10)

    results = service.search_forums("Test Topic Normal", user, date_to=past)

    assert topic not in _all(results["topic"])


def test_search_forums_filters_by_locked_state(
    request_context, topic, topic_locked, user
):
    results = service.search_forums("Test", user, state="locked")

    topics = _all(results["topic"])
    assert topic_locked in topics
    assert topic not in topics


def test_search_forums_locked_state_applies_to_posts_too(
    request_context, topic, topic_locked, user
):
    results = service.search_forums("Test", user, content_type="post", state="locked")

    posts = _all(results["post"])
    assert topic_locked.first_post in posts
    assert topic.first_post not in posts


def test_search_forums_hidden_state_requires_viewhidden(
    request_context, topic, user, admin_user
):
    cache.clear()  # see comment in test_search_form_forum_choices_are_permission_scoped

    topic.hide(user=admin_user)
    topic.save()

    # Without `viewhidden`, the hidden state filter is ignored and the
    # topic stays excluded by the default hidden-content behavior.
    results = service.search_forums("Test Topic Normal", user, state="hidden")
    assert _all(results["topic"]) == []

    # With `viewhidden`, the explicit filter surfaces it.
    results = service.search_forums("Test Topic Normal", admin_user, state="hidden")
    assert topic in _all(results["topic"])


@contextmanager
def _csrf_disabled(application):
    """Search views build their form from `request.form` via
    `self.form()`, so exercising `.post()` end-to-end needs a real form
    submission - which would otherwise be rejected by Flask-WTF's CSRF
    check.
    """
    original = application.config["WTF_CSRF_ENABLED"]
    application.config["WTF_CSRF_ENABLED"] = False
    try:
        yield
    finally:
        application.config["WTF_CSRF_ENABLED"] = original


def test_search_view_finds_topic(application, topic, user):
    view = views.Search.as_view("search")

    with _csrf_disabled(application):
        with application.test_request_context(
            method="POST",
            data={
                "search_query": "Test Topic Normal",
                "search_type": "forum",
                "submit": "Search",
            },
        ):
            login_user(user)
            resp = view()
            assert topic.title in resp
