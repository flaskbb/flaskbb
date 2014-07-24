import pytest

from flaskbb.user.models import User, Guest

@pytest.fixture
def guest():
    """Return a guest (not logged in) user."""
    return Guest()


@pytest.fixture
def user(default_groups):
    """Creates a user with normal permissions."""
    user = User(username="test_normal", email="test_normal@example.org",
                password="test", primary_group_id=default_groups[3].id)
    user.save()
    return user


@pytest.fixture
def moderator_user(user, forum, default_groups):
    """Creates a test user with moderator permissions."""

    user = User(username="test_mod", email="test_mod@example.org",
                password="test", primary_group_id=default_groups[2].id)
    user.save()

    forum.moderators.append(user)
    forum.save()
    return user


@pytest.fixture
def admin_user(default_groups):
    """Creates a admin user."""
    user = User(username="test_admin", email="test_admin@example.org",
                password="test", primary_group_id=default_groups[0].id)
    user.save()
    return user


@pytest.fixture
def super_moderator_user(default_groups):
    """Creates a super moderator user."""
    user = User(username="test_super_mod", email="test_super@example.org",
                password="test", primary_group_id=default_groups[1].id)
    user.save()
    return user
