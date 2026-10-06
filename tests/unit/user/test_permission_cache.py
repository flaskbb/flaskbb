"""The permissions of an identity are snapshotted once per request and
cached across requests under a version every group change bumps.
"""

from flaskbb.core.auth.permissions import forget_permissions, permissions_for
from flaskbb.user.models import Group, GroupRole, permissions_version

ADMINISTRATOR, SUPER_MODERATOR, MODERATOR, MEMBER, BANNED, GUEST = range(6)


def test_permissions_are_snapshotted_once_per_request(user):
    assert permissions_for(user) is permissions_for(user)
    assert user.permissions is permissions_for(user).granted


def test_guests_share_one_snapshot(guest, default_groups):
    assert permissions_for(guest) is permissions_for(guest)
    assert not guest.permissions["posttopic"]


def test_invalidating_a_user_forgets_the_snapshot(user):
    stale = permissions_for(user)
    user.invalidate_cache()
    assert permissions_for(user) is not stale


def test_forgetting_the_snapshots_rebuilds_them(user):
    stale = permissions_for(user)
    forget_permissions()
    assert permissions_for(user) is not stale


def test_saving_a_group_starts_a_new_cache_generation(default_groups):
    before = permissions_version()
    default_groups[MEMBER].save()
    assert permissions_version() == before + 1


def test_a_group_change_reaches_its_members_at_once(user, default_groups):
    assert not user.permissions["deletepost"]

    default_groups[MEMBER].set_permission("deletepost", True)
    default_groups[MEMBER].save()

    assert user.permissions["deletepost"]


def test_a_group_change_reaches_guests_at_once(guest, default_groups):
    assert not guest.permissions["posttopic"]

    default_groups[GUEST].set_permission("posttopic", True)
    default_groups[GUEST].save()

    assert guest.permissions["posttopic"]


def test_deleting_a_group_starts_a_new_cache_generation(database, default_groups):
    extra = Group(name="Extra").save()
    before = permissions_version()
    extra.delete()
    assert permissions_version() == before + 1


def test_changing_a_users_groups_reaches_the_user_at_once(user, default_groups):
    assert all(group.role is not GroupRole.ADMINISTRATOR for group in user.groups)

    user.save(groups=[default_groups[ADMINISTRATOR]])

    assert any(group.role is GroupRole.ADMINISTRATOR for group in user.groups)


def test_banning_reaches_the_user_at_once(user, default_groups):
    assert not user.is_banned
    user.ban()
    assert user.is_banned
    user.unban()
    assert not user.is_banned


def test_moderator_lookup_is_cached_within_the_snapshot(moderator_user, forum):
    permissions = permissions_for(moderator_user)
    assert permissions.moderates(forum)

    forum.moderators = []
    forum.save()

    assert permissions.moderates(forum)
    forget_permissions()
    assert not permissions_for(moderator_user).moderates(forum)
