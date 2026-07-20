import pytest

from flaskbb.core.search import tantivy as tantivy_module
from flaskbb.core.search.tantivy import TantivyBackend
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
