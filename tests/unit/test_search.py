import importlib.util
from pathlib import Path

import pytest
from flaskbb.core.search import FlaskBBSearch, SearchBackendRegistration
from flaskbb.core.search.backends.postgresql import PostgreSQLSearchBackend
from flaskbb.core.search.backends.sql import SQLSearchBackend
from flaskbb.core.search.backends.sqlite import SQLiteSearchBackend
from flaskbb.core.search.base import ordered_by_ids, SearchBackend
from flaskbb.core.settings import flaskbb_config
from flaskbb.extensions import db, pluggy
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.plugins.models import PluginRegistry
from flaskbb.user.models import User
from pluggy import HookimplMarker
from sqlalchemy import text

impl = HookimplMarker("flaskbb")


class _DummyBackend(SearchBackend):
    def index(self, instance):
        pass

    def update(self, instance):
        pass

    def remove(self, instance):
        pass

    def reindex(self, models=None):
        pass

    def search(self, model, query):
        return ordered_by_ids(model, [])


class _SearchPlugin:
    def __init__(self, registration):
        self._registration = registration

    @impl
    def flaskbb_load_search_backends(self):
        return self._registration


def _all(stmt):
    return db.session.scalars(stmt).unique().all()


def _load_fts_migration():
    path = (
        Path(__file__).parents[2]
        / "flaskbb"
        / "migrations"
        / "202607211500_1784625534_add_fts_search_indexes.py"
    )
    spec = importlib.util.spec_from_file_location("_fts_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def sqlite_fts(database):
    """Applies the SQLite FTS5 schema (virtual tables + sync triggers) the
    migration would create, since the test DB is built via create_all(),
    not migrations.
    """
    migration = _load_fts_migration()
    for statement in migration.sqlite_upgrade_sql():
        db.session.execute(text(statement))
    db.session.commit()
    yield
    for statement in migration.sqlite_downgrade_sql():
        db.session.execute(text(statement))
    db.session.commit()


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

    page = db.paginate(backend.search(User, "test_normal"), page=1, per_page=10, error_out=False)
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


def test_plugin_can_register_search_backend(application):
    plugin = _SearchPlugin(SearchBackendRegistration("dummy", _DummyBackend))
    pluggy.register(plugin)
    application.config["SEARCH_BACKEND"] = "dummy"

    try:
        proxy = FlaskBBSearch(pluggy)
        proxy.init_app(application)
        assert isinstance(proxy._impl, _DummyBackend)
    finally:
        pluggy.unregister(plugin)
        del application.config["SEARCH_BACKEND"]


def test_plugin_backend_colliding_with_builtin_raises(application):
    plugin = _SearchPlugin(SearchBackendRegistration("sql", _DummyBackend))
    pluggy.register(plugin)

    try:
        # Selected backend is the default "sql", but the collision is still
        # caught because plugin backends are always validated.
        proxy = FlaskBBSearch(pluggy)
        with pytest.raises(ValueError, match="built-in"):
            proxy.init_app(application)
    finally:
        pluggy.unregister(plugin)


def test_unknown_backend_error_lists_plugin_names(application):
    plugin = _SearchPlugin(SearchBackendRegistration("dummy", _DummyBackend))
    pluggy.register(plugin)
    application.config["SEARCH_BACKEND"] = "does-not-exist"

    try:
        proxy = FlaskBBSearch(pluggy)
        with pytest.raises(ValueError, match="dummy"):
            proxy.init_app(application)
    finally:
        pluggy.unregister(plugin)
        del application.config["SEARCH_BACKEND"]


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


def test_sqlite_search_post_by_content(sqlite_fts, topic):
    post = topic.first_post
    backend = SQLiteSearchBackend()

    assert post in _all(backend.search(Post, "Content Normal"))
    assert _all(backend.search(Post, "nonexistentterm")) == []


def test_sqlite_search_is_case_insensitive(sqlite_fts, topic):
    post = topic.first_post
    backend = SQLiteSearchBackend()

    assert post in _all(backend.search(Post, "content normal"))


def test_sqlite_search_topic_by_title(sqlite_fts, topic):
    backend = SQLiteSearchBackend()

    assert topic in _all(backend.search(Topic, "Test Topic Normal"))


def test_sqlite_search_topic_by_first_post_content(sqlite_fts, topic):
    """A topic must be findable by its opening post's body, matched
    through posts_fts, mirroring the sql backend.
    """
    backend = SQLiteSearchBackend()

    assert topic in _all(backend.search(Topic, "Content Normal"))


def test_sqlite_search_forum(sqlite_fts, forum):
    backend = SQLiteSearchBackend()

    assert forum in _all(backend.search(Forum, "Test Forum"))


def test_sqlite_search_user(sqlite_fts, user):
    backend = SQLiteSearchBackend()

    assert user in _all(backend.search(User, "test_normal"))


def test_sqlite_search_empty_query_returns_nothing(sqlite_fts, user):
    backend = SQLiteSearchBackend()

    assert _all(backend.search(User, "")) == []


def test_sqlite_search_reflects_updates_via_triggers(sqlite_fts, topic):
    post = topic.first_post
    backend = SQLiteSearchBackend()

    assert _all(backend.search(Post, "zebra")) == []

    post.content = "a zebra appeared"
    post.save()

    assert post in _all(backend.search(Post, "zebra"))


def test_sqlite_reindex_backfills(sqlite_fts, topic):
    backend = SQLiteSearchBackend()

    backend.reindex()

    assert topic.first_post in _all(backend.search(Post, "Content Normal"))


def test_sqlite_search_unknown_model_raises(sqlite_fts):
    backend = SQLiteSearchBackend()

    with pytest.raises(ValueError):
        backend.search(PluginRegistry, "whatever")


def test_sqlite_lifecycle_write_methods_are_noops(sqlite_fts, user):
    backend = SQLiteSearchBackend()

    assert backend.index(user) is None
    assert backend.update(user) is None
    assert backend.remove(user) is None


def test_create_all_builds_sqlite_fts_schema(application):
    """A fresh install (db.create_all() + stamp, no migration run) must
    still produce the FTS schema when the sqlite backend is active.
    """
    application.config["SEARCH_BACKEND"] = "sqlite"
    try:
        db.create_all()
        tables = (
            db.session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='posts_fts'")
            )
            .scalars()
            .all()
        )
        triggers = (
            db.session.execute(text("SELECT name FROM sqlite_master WHERE type='trigger'"))
            .scalars()
            .all()
        )
        assert "posts_fts" in tables
        assert "posts_ai" in triggers
    finally:
        migration = _load_fts_migration()
        for statement in migration.sqlite_downgrade_sql():
            db.session.execute(text(statement))
        db.session.commit()
        db.drop_all()
        del application.config["SEARCH_BACKEND"]


def test_create_all_skips_fts_schema_for_other_backends(database):
    """With a non-FTS backend selected (default 'sql'), create_all must
    not build the FTS tables - the DDL guard keeps them out.
    """
    tables = (
        db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='posts_fts'")
        )
        .scalars()
        .all()
    )
    assert tables == []


def test_flaskbb_search_proxy_resolves_sqlite(application):
    application.config["SEARCH_BACKEND"] = "sqlite"
    proxy = FlaskBBSearch()

    try:
        proxy.init_app(application)
        assert isinstance(proxy._impl, SQLiteSearchBackend)
    finally:
        del application.config["SEARCH_BACKEND"]


def test_flaskbb_search_proxy_resolves_postgresql(application):
    application.config["SEARCH_BACKEND"] = "postgresql"
    proxy = FlaskBBSearch()

    try:
        proxy.init_app(application)
        assert isinstance(proxy._impl, PostgreSQLSearchBackend)
    finally:
        del application.config["SEARCH_BACKEND"]
