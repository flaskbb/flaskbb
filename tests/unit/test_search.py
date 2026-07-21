import pytest

from flaskbb.core.search import FlaskBBSearch
from flaskbb.core.search.sql import SQLSearchBackend
from flaskbb.core.settings import flaskbb_config
from flaskbb.extensions import db
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.plugins.models import PluginRegistry
from flaskbb.user.models import User


def _all(stmt):
    return db.session.scalars(stmt).unique().all()


def test_search_post(topic):
    post = topic.first_post
    backend = SQLSearchBackend()

    result = backend.search(Post, "Content Normal")
    assert post in _all(result)

    assert _all(backend.search(Post, "nonexistent-term")) == []


def test_search_post_case_insensitive(topic):
    post = topic.first_post
    backend = SQLSearchBackend()

    assert post in _all(backend.search(Post, "content normal"))


def test_search_topic_by_title(topic):
    backend = SQLSearchBackend()

    result = backend.search(Topic, "Test Topic Normal")
    assert topic in _all(result)


def test_search_topic_by_first_post_content(topic):
    """Regression guard for the relationship-traversal case: a topic's
    first post content must be searchable, mirroring what the old
    TopicWhoosheer did via `topic.first_post.content`.
    """
    backend = SQLSearchBackend()

    result = backend.search(Topic, "Content Normal")
    assert topic in _all(result)


def test_search_forum(forum):
    backend = SQLSearchBackend()

    result = backend.search(Forum, "Test Forum")
    assert forum in _all(result)


def test_search_user(user):
    backend = SQLSearchBackend()

    result = backend.search(User, "test_normal")
    assert user in _all(result)


def test_search_result_supports_pagination(user):
    backend = SQLSearchBackend()

    page = db.paginate(
        backend.search(User, "test_normal"), page=1, per_page=10, error_out=False
    )
    assert user in page.items


def test_search_escapes_like_wildcards(database, category, default_groups):
    forum_percent = Forum(title="50% off", category_id=category.id)
    forum_percent.groups = default_groups
    forum_percent.save()

    forum_other = Forum(title="something else", category_id=category.id)
    forum_other.groups = default_groups
    forum_other.save()

    backend = SQLSearchBackend()

    result = _all(backend.search(Forum, "50% off"))
    assert forum_percent in result
    assert forum_other not in result


def test_search_unknown_model_raises():
    backend = SQLSearchBackend()

    with pytest.raises(ValueError):
        backend.search(PluginRegistry, "whatever")


def test_search_lifecycle_methods_are_noops(user):
    backend = SQLSearchBackend()

    assert backend.index(user) is None
    assert backend.update(user) is None
    assert backend.remove(user) is None
    assert backend.reindex() is None


def test_search_multi_returns_only_requested_keys(user, topic):
    backend = SQLSearchBackend()

    results = backend.search_multi({"user": User, "topic": Topic}, "test")
    assert set(results.keys()) == {"user", "topic"}


def test_flaskbb_search_proxy_defaults_to_sql(application):
    proxy = FlaskBBSearch()
    proxy.init_app(application)
    assert isinstance(proxy._impl, SQLSearchBackend)


def test_flaskbb_search_proxy_rejects_unknown_backend(application):
    application.config["SEARCH_BACKEND"] = "does-not-exist"
    proxy = FlaskBBSearch()

    with pytest.raises(ValueError):
        proxy.init_app(application)

    del application.config["SEARCH_BACKEND"]


def test_flaskbb_search_proxy_requires_init_app():
    proxy = FlaskBBSearch()

    with pytest.raises(RuntimeError):
        proxy.search(User, "test")


def test_snippet_wraps_match_in_mark(database):
    backend = SQLSearchBackend()

    result = backend.snippet(Post, 1, "hello world test content here", "world")
    assert "<mark>world</mark>" in result


def test_snippet_is_case_insensitive(database):
    backend = SQLSearchBackend()

    result = backend.snippet(Post, 1, "Hello World", "world")
    assert "<mark>World</mark>" in result


def test_snippet_escapes_html(database):
    backend = SQLSearchBackend()

    result = backend.snippet(Post, 1, "<script>alert(1)</script> test", "test")
    assert "<script>" not in result
    assert "&lt;script&gt;" in result


def test_snippet_no_match_returns_cropped_unhighlighted(default_settings):
    backend = SQLSearchBackend()
    flaskbb_config["SEARCH_SNIPPET_LENGTH"] = 10

    try:
        result = backend.snippet(Post, 1, "no match here at all in this text", "zzz")
        assert "<mark>" not in result
        assert len(result) <= 10
    finally:
        flaskbb_config["SEARCH_SNIPPET_LENGTH"] = 320


def test_snippet_zero_length_shows_full_content(default_settings):
    backend = SQLSearchBackend()
    flaskbb_config["SEARCH_SNIPPET_LENGTH"] = 0

    try:
        content = ("a" * 500) + "test" + ("b" * 500)
        result = backend.snippet(Post, 1, content, "test")
        assert result.startswith("a" * 500)
        assert result.endswith("b" * 500)
        assert "<mark>test</mark>" in result
    finally:
        flaskbb_config["SEARCH_SNIPPET_LENGTH"] = 320


def test_snippet_windows_around_match_with_ellipses(default_settings):
    backend = SQLSearchBackend()
    flaskbb_config["SEARCH_SNIPPET_LENGTH"] = 20

    try:
        content = ("a" * 500) + "test" + ("b" * 500)
        result = backend.snippet(Post, 1, content, "test")
        assert result.startswith("…")
        assert result.endswith("…")
        assert "<mark>test</mark>" in result
        assert len(result) < len(content)
    finally:
        flaskbb_config["SEARCH_SNIPPET_LENGTH"] = 320


def test_flaskbb_search_proxy_resolves_tantivy(application, tmp_path):
    from flaskbb.core.search import tantivy as tantivy_module
    from flaskbb.core.search.tantivy import TantivyBackend

    application.config["SEARCH_BACKEND"] = "tantivy"
    application.config["SEARCH_INDEX_DIR"] = str(tmp_path / "search_index")
    proxy = FlaskBBSearch()

    try:
        proxy.init_app(application)
        assert isinstance(proxy._impl, TantivyBackend)
    finally:
        del application.config["SEARCH_BACKEND"]
        tantivy_module._active = None
