import pytest

from flaskbb.core.search import tantivy as tantivy_module
from flaskbb.core.search.tantivy import TantivyBackend
from flaskbb.core.settings import flaskbb_config
from flaskbb.extensions import db
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.plugins.models import PluginRegistry
from flaskbb.user.models import User


def _all(stmt):
    return db.session.scalars(stmt).unique().all()


@pytest.fixture
def tantivy_backend(application, tmp_path):
    """A TantivyBackend bound to a throwaway index directory.

    init_app() also sets the tantivy module's `_active` global, which
    drives automatic indexing on commit (see tantivy.py's docstring) -
    resetting it back to None after the test keeps this fixture from
    leaking session-event side effects into unrelated tests that share
    the same worker process and the same package-scoped `application`
    (e.g. tests/unit/test_search.py, which never activates tantivy but
    still commits rows via its own fixtures).
    """
    application.config["SEARCH_INDEX_DIR"] = str(tmp_path / "search_index")
    backend = TantivyBackend()
    backend.init_app(application)
    yield backend
    tantivy_module._active = None


def test_index_and_search_post(tantivy_backend, topic):
    post = topic.first_post
    tantivy_backend.index(post)

    assert post in _all(tantivy_backend.search(Post, "Content Normal"))
    assert _all(tantivy_backend.search(Post, "nonexistent-term")) == []


def test_search_topic_by_title(tantivy_backend, topic):
    tantivy_backend.index(topic)

    assert topic in _all(tantivy_backend.search(Topic, "Test Topic Normal"))


def test_search_topic_by_first_post_content(tantivy_backend, topic):
    """Regression guard for the relationship-traversal case: a topic's
    first post content must be searchable, mirroring what the old
    TopicWhoosheer (and the SQL backend's `Topic.first_post.has(...)`)
    did via `topic.first_post.content`.
    """
    tantivy_backend.index(topic)

    assert topic in _all(tantivy_backend.search(Topic, "Content Normal"))


def test_search_forum(tantivy_backend, forum):
    tantivy_backend.index(forum)

    assert forum in _all(tantivy_backend.search(Forum, "Test Forum"))


def test_search_user(tantivy_backend, user):
    tantivy_backend.index(user)

    assert user in _all(tantivy_backend.search(User, "test_normal"))


def test_search_result_supports_pagination(tantivy_backend, user):
    tantivy_backend.index(user)

    page = db.paginate(
        tantivy_backend.search(User, "test_normal"),
        page=1,
        per_page=10,
        error_out=False,
    )
    assert user in page.items


def test_update_reindexes_and_old_value_no_longer_matches(tantivy_backend, user):
    tantivy_backend.index(user)
    assert user in _all(tantivy_backend.search(User, user.email))

    old_email = user.email
    user.email = "changed@example.org"
    user.save()
    tantivy_backend.update(user)

    assert _all(tantivy_backend.search(User, old_email)) == []
    assert user in _all(tantivy_backend.search(User, "changed@example.org"))


def test_remove_drops_from_index(tantivy_backend, user):
    tantivy_backend.index(user)
    assert user in _all(tantivy_backend.search(User, "test_normal"))

    tantivy_backend.remove(user)

    assert _all(tantivy_backend.search(User, "test_normal")) == []


def test_reindex_rebuilds_from_database(tantivy_backend, user, topic):
    # Deliberately not calling index() first - reindex() must find
    # these rows itself by querying the database.
    tantivy_backend.reindex()

    assert user in _all(tantivy_backend.search(User, "test_normal"))
    assert topic in _all(tantivy_backend.search(Topic, "Content Normal"))


def test_reindex_scoped_to_given_models_only(user, topic, tantivy_backend):
    # user/topic are created (and committed) before tantivy_backend
    # activates, so nothing has been auto-indexed yet - reindex(
    # models=[User]) below is the only thing that can populate either
    # index, and it's scoped to User only.
    tantivy_backend.reindex(models=[User])

    assert user in _all(tantivy_backend.search(User, "test_normal"))
    assert _all(tantivy_backend.search(Topic, "Test Topic Normal")) == []


def test_search_unknown_model_raises(tantivy_backend):
    with pytest.raises(ValueError):
        tantivy_backend.search(PluginRegistry, "whatever")


def test_snippet_uses_stored_content_field(tantivy_backend, topic):
    post = topic.first_post
    tantivy_backend.index(post)

    result = tantivy_backend.snippet(Post, post.id, post.content, "Content")
    assert "<mark>Content</mark>" in result


def test_snippet_falls_back_when_match_is_outside_content(tantivy_backend, topic):
    """The post author's username only lives in the `username` field,
    not `content` - Tantivy's own snippet generator then has nothing to
    highlight, so this must fall back to the generic base implementation
    instead of returning an empty snippet.
    """
    post = topic.first_post
    tantivy_backend.index(post)

    result = tantivy_backend.snippet(Post, post.id, post.content, post.username)
    assert result


def test_snippet_falls_back_for_unindexed_pk(tantivy_backend, topic):
    post = topic.first_post
    # Deliberately never indexed.

    result = tantivy_backend.snippet(Post, post.id, post.content, "Content")
    assert "<mark>Content</mark>" in result


def test_snippet_zero_length_uses_fallback_for_full_content(tantivy_backend, topic):
    post = topic.first_post
    tantivy_backend.index(post)
    flaskbb_config["SEARCH_SNIPPET_LENGTH"] = 0

    try:
        result = tantivy_backend.snippet(Post, post.id, post.content, "Content")
        # SEARCH_SNIPPET_LENGTH == 0 has no native Tantivy equivalent
        # ("unbounded"), so this always falls back to the base
        # implementation, which returns the full, unbounded content.
        assert result == "Test <mark>Content</mark> Normal"
    finally:
        flaskbb_config["SEARCH_SNIPPET_LENGTH"] = 320


def test_commit_automatically_syncs_the_index(tantivy_backend, forum, user):
    """The whole point of session-event-driven indexing: no explicit
    index()/update()/remove() call at all here - just ordinary
    model.save()/.delete() - and the index still stays in sync.
    """
    # Distinct, non-overlapping words in the title vs. the post content:
    # tantivy's query parser ORs multi-word queries by default, so a
    # query for the old title must not accidentally still match via a
    # leftover word from the (unchanged) post content.
    topic = Topic(title="Zylophone")
    post = Post(content="Marmoset")
    topic.save(forum=forum, user=user, post=post)

    assert topic in _all(tantivy_backend.search(Topic, "Zylophone"))

    topic.title = "Quixotic"
    topic.save()

    assert _all(tantivy_backend.search(Topic, "Zylophone")) == []
    assert topic in _all(tantivy_backend.search(Topic, "Quixotic"))


def test_bulk_delete_leaves_a_stale_but_harmless_index_entry(
    tantivy_backend, database, user
):
    """Documents a known, accepted limitation (see the module
    docstring): a bulk `delete()` bypasses ORM session events entirely,
    so the tantivy index isn't told about it - but search() re-verifies
    every match against the database, so the now-deleted row never
    actually appears in results despite the stale index entry.
    """
    tantivy_backend.index(user)
    assert user in _all(tantivy_backend.search(User, "test_normal"))

    database.session.execute(db.delete(User).where(User.id == user.id))
    database.session.commit()

    assert _all(tantivy_backend.search(User, "test_normal")) == []


@pytest.fixture
def reader_only_backend(application, tmp_path):
    """A TantivyBackend with SEARCH_INDEX_WRITER=False - has read-only
    Index objects but no IndexWriter, simulating a web worker in a
    multi-process deployment where a single Celery worker owns writes.
    """
    application.config["SEARCH_INDEX_DIR"] = str(tmp_path / "search_index")
    application.config["SEARCH_INDEX_WRITER"] = False
    backend = TantivyBackend()
    backend.init_app(application)
    yield backend
    application.config["SEARCH_INDEX_WRITER"] = True
    tantivy_module._active = None


def test_index_raises_without_a_local_writer(user, reader_only_backend):
    # `user` must be created (and committed) before reader_only_backend
    # activates - otherwise its own creation would be routed through
    # the (here unmocked) Celery dispatch path below, in this same
    # process, and crash for the same reason this test is checking for.
    with pytest.raises(RuntimeError, match="SEARCH_INDEX_WRITER=False"):
        reader_only_backend.index(user)


def test_reindex_raises_without_a_local_writer(reader_only_backend):
    with pytest.raises(RuntimeError, match="SEARCH_INDEX_WRITER=False"):
        reader_only_backend.reindex()


def test_after_commit_dispatches_to_celery_instead_of_writing_locally(
    topic, monkeypatch, reader_only_backend
):
    """The whole point of SEARCH_INDEX_WRITER=False: `_after_commit` must
    not attempt a local write (there's no writer to use) - it hands the
    pending write to the Celery task that runs on the writer process.

    `topic` is created before reader_only_backend activates, same reason
    as test_index_raises_without_a_local_writer above.
    """
    dispatched = []
    monkeypatch.setattr(
        tantivy_module._apply_pending_task, "delay", dispatched.append
    )

    topic.title = "Marsupial Habitat"
    topic.save()

    assert len(dispatched) == 1
    names = {name for name, _pk, _fields in dispatched[0]["write"]}
    assert "Topic" in names


def test_apply_pending_task_round_trip_writes_on_the_writer_process(
    tantivy_backend, topic
):
    """Simulates what actually runs on the Celery worker: the serialized
    payload `_after_commit` would hand to `.delay()`, deserialized and
    applied against the writer-owning backend's real IndexWriter.
    """
    pending = {
        "write": [(Topic, topic.id, ("Marsupial", topic.username, ""))],
        "remove": [],
    }
    payload = tantivy_module._serialize_pending(pending)
    assert payload["write"][0][0] == "Topic"

    tantivy_module._apply_pending_task(payload)

    assert topic in _all(tantivy_backend.search(Topic, "Marsupial"))
