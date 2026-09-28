import pytest
from flaskbb.extensions import limiter
from flaskbb.user.models import User


@pytest.fixture
def lookup_users(default_groups):
    def create(username, activated=True):
        user = User(
            username=username,
            email=f"{username.replace(' ', '')}@example.org",
            password="test",
            primary_group=default_groups[3],
            activated=activated,
        )
        user.save()
        return user

    return create


@pytest.fixture
def client(application):
    limiter.reset()
    with application.test_client() as client:
        yield client
    limiter.reset()


def login(client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True


def lookup(client, **params):
    resp = client.get("/user/lookup/usernames", query_string=params)
    assert resp.status_code == 200
    return [entry["username"] for entry in resp.get_json()]


def test_requires_login(client, user, default_settings):
    resp = client.get("/user/lookup/usernames", query_string={"q": "test"})

    assert resp.status_code in (302, 401)


def test_needs_three_characters(client, user, default_settings):
    login(client, user)

    assert lookup(client, q="te") == []
    assert lookup(client, q="  te  ") == []
    assert lookup(client, q="tes") == ["test_normal"]


def test_prefix_match_ignores_case(client, user, lookup_users, default_settings):
    lookup_users("Alice")
    lookup_users("alicent")
    lookup_users("malice")
    login(client, user)

    assert lookup(client, q="ALI") == ["Alice", "alicent"]


def test_like_wildcards_are_literal(client, user, lookup_users, default_settings):
    lookup_users("abcdef")
    login(client, user)

    assert lookup(client, q="a_c") == []
    assert lookup(client, q="ab%") == []


def test_exact_match_comes_first(client, user, lookup_users, default_settings):
    lookup_users("bobby")
    lookup_users("bob")
    lookup_users("bobbette")
    login(client, user)

    assert lookup(client, q="bob") == ["bob", "bobby", "bobbette"]


def test_limits_results(client, user, lookup_users, default_settings):
    for i in range(12):
        lookup_users(f"many{i:02}")
    login(client, user)

    assert len(lookup(client, q="many")) == 10


def test_hides_unactivated_users(client, user, lookup_users, default_settings):
    lookup_users("carol_inactive", activated=False)
    login(client, user)

    assert lookup(client, q="carol") == []


def test_hides_unmentionable_usernames(client, user, lookup_users, default_settings):
    lookup_users("dave smith")
    lookup_users("dave.jones")
    lookup_users("dave-ok")
    login(client, user)

    assert lookup(client, q="dave") == ["dave-ok"]
    assert lookup(client, q="dave smith") == []


def test_exclude_self(client, user, default_settings):
    login(client, user)

    assert lookup(client, q="test_normal") == ["test_normal"]
    assert lookup(client, q="test_normal", exclude_self="1") == []


def test_returns_profile_and_default_avatar(client, user, default_settings):
    login(client, user)

    resp = client.get("/user/lookup/usernames", query_string={"q": "test_normal"})

    assert resp.get_json() == [
        {
            "username": "test_normal",
            "url": "/user/test_normal",
            "avatar_url": "/static/avatar100x100.png",
        }
    ]
