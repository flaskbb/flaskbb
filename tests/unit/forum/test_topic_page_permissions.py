"""The topic page shows administrators a ban button per author, which must
not cost a query per author.
"""

import pytest
from flask_login.test_client import FlaskLoginClient
from flaskbb.extensions import cache
from flaskbb.forum.models import Post
from flaskbb.permissions import permission_manager
from flaskbb.user.models import User


@pytest.fixture
def authors(default_groups):
    users = []
    for number in range(5):
        user = User(
            username=f"author{number}",
            email=f"author{number}@example.org",
            password="test",
            primary_group=default_groups[3],
            activated=True,
        )
        users.append(user.save())
    return users


@pytest.fixture
def busy_topic(topic, authors):
    for author in authors:
        Post(content=f"Reply by {author.username}").save(user=author, topic=topic)
    return topic


@pytest.fixture
def client(application, admin_user):
    application.test_client_class = FlaskLoginClient
    return application.test_client(user=admin_user)


def _per_user_membership_queries(selects):
    return sum("groups_users.user_id = ?" in statement for statement in selects)


def _batched_membership_queries(selects):
    return sum("groups_users.user_id IN (" in statement for statement in selects)


def test_topic_page_loads_the_authors_groups_in_one_query(client, busy_topic, authors, selects):
    cache.clear()
    selects.clear()

    response = client.get(f"/topic/{busy_topic.id}")

    assert response.status_code == 200
    for author in authors:
        assert f"/admin/users/{author.id}/ban".encode() in response.data
    assert _batched_membership_queries(selects) == 1
    assert _per_user_membership_queries(selects) == 0


def test_warm_topic_page_still_loads_the_authors_groups_in_one_query(
    client, busy_topic, authors, selects
):
    client.get(f"/topic/{busy_topic.id}")
    # the test client shares the test's app context, so reset ``g`` by hand
    permission_manager.forget()
    selects.clear()

    response = client.get(f"/topic/{busy_topic.id}")

    assert response.status_code == 200
    assert _batched_membership_queries(selects) == 1
    assert _per_user_membership_queries(selects) == 0
