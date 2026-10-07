"""The permissions of an identity are snapshotted once per request. Groups
and their permissions are cached across requests under a version every group
change bumps; membership is read once per request for every loaded user.
"""

from flaskbb.core.auth.permissions import forget_permissions, permissions_for
from flaskbb.extensions import cache, db
from flaskbb.user.models import forget_memberships, Group, GroupRole, permissions_version, User
from flaskbb.utils import requirements as r

ADMINISTRATOR, SUPER_MODERATOR, MODERATOR, MEMBER, BANNED, GUEST = range(6)


def next_request():
    """The test client shares the test's app context, so ``g`` has to be
    reset by hand to behave like a new request.
    """
    forget_memberships()
    forget_permissions()


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


def test_changing_the_primary_group_reaches_the_user_at_once(user, default_groups):
    assert all(group.role is not GroupRole.ADMINISTRATOR for group in user.groups)

    user.primary_group_id = default_groups[ADMINISTRATOR].id
    user.save()

    assert any(group.role is GroupRole.ADMINISTRATOR for group in user.groups)


def test_adding_a_secondary_group_reaches_the_user_at_once(user, default_groups):
    assert all(group.role is not GroupRole.MODERATOR for group in user.groups)

    user.add_to_group(default_groups[MODERATOR])
    user.save()

    assert any(group.role is GroupRole.MODERATOR for group in user.groups)


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


def test_repeated_checks_within_a_request_do_not_query(user, forum, selects):
    assert r.Has("postreply")(user)
    assert r.can_access_forum(forum)(user)
    assert not r.can_moderate(forum)(user)
    selects.clear()

    for _ in range(50):
        assert r.Has("postreply")(user)
        assert not r.IsAdmin(user)
        assert r.can_access_forum(forum)(user)
        assert not r.can_moderate(forum)(user)

    assert selects == []


def test_warm_request_takes_only_the_membership_query(user, selects):
    assert user.permissions["postreply"]
    assert permissions_for(user).group_ids
    next_request()
    selects.clear()

    assert user.permissions["postreply"]
    assert not r.IsAdmin(user)
    assert permissions_for(user).group_ids

    assert len(selects) == 1
    assert "FROM groups_users" in selects[0]


def test_warm_guest_request_does_not_query_the_database(guest, default_groups, selects):
    assert not guest.permissions["postreply"]
    next_request()
    selects.clear()

    assert not guest.permissions["postreply"]
    assert not r.IsAtleastModerator(guest)

    assert selects == []


def test_saving_a_group_does_not_load_its_members(user, default_groups, selects):
    assert not user.permissions["deletepost"]
    selects.clear()

    default_groups[MEMBER].set_permission("deletepost", True)
    default_groups[MEMBER].save()

    assert not any("FROM users" in statement for statement in selects)
    assert user.permissions["deletepost"]


def test_loading_a_group_does_not_load_its_permission_rows(user, selects):
    db.session.expire_all()
    selects.clear()

    assert user.primary_group.name == "Member"

    assert not any("FROM group_permissions" in statement for statement in selects)


def test_cold_permissions_take_a_single_rows_query(user, default_groups, selects):
    user.save(groups=[default_groups[MODERATOR]])
    cache.clear()
    forget_permissions()
    selects.clear()

    assert user.permissions["mod_banuser"]

    assert sum("FROM group_permissions" in statement for statement in selects) == 1


def test_cold_guest_permissions_need_no_membership_query(guest, default_groups, selects):
    cache.clear()
    forget_permissions()
    selects.clear()

    assert not guest.permissions["postreply"]

    assert not any("FROM groups_users" in statement for statement in selects)


def test_group_tables_are_loaded_once_for_every_identity(user, moderator_user, guest, selects):
    cache.clear()
    forget_permissions()
    selects.clear()

    assert user.permissions["postreply"]
    assert moderator_user.permissions["mod_banuser"]
    assert not guest.permissions["postreply"]

    assert sum("FROM group_permissions" in statement for statement in selects) == 1
    assert sum(_loads_groups(statement) for statement in selects) == 1


def test_checking_many_loaded_users_takes_one_membership_query(
    user, moderator_user, admin_user, super_moderator_user, default_groups, selects
):
    user.save(groups=[default_groups[MODERATOR]])
    cache.clear()
    forget_permissions()
    selects.clear()

    assert r.can_ban_user(user)(super_moderator_user)
    assert r.can_ban_user(moderator_user)(super_moderator_user)
    assert not r.can_ban_user(admin_user)(super_moderator_user)
    assert not r.can_ban_user(super_moderator_user)(moderator_user)
    assert permissions_for(user).rank == GroupRole.MODERATOR.rank
    assert user.permissions["mod_banuser"]
    assert not user.is_banned

    assert sum("FROM groups_users" in statement for statement in selects) == 1
    assert sum(_loads_groups(statement) for statement in selects) == 1
    assert sum("FROM group_permissions" in statement for statement in selects) == 1


def test_a_user_loaded_later_costs_one_more_membership_query(user, default_groups, selects):
    assert user.permissions["postreply"]
    selects.clear()

    later = User(
        username="latecomer",
        email="latecomer@example.org",
        password="test",
        primary_group=default_groups[MEMBER],
        activated=True,
    ).save()
    assert later.permissions["postreply"]
    assert later.permissions["postreply"]

    assert sum("FROM groups_users" in statement for statement in selects) == 1


def test_changing_the_groups_within_a_request_reloads_the_membership(user, default_groups):
    assert not user.permissions["mod_banuser"]

    user.save(groups=[default_groups[MODERATOR]])

    assert user.permissions["mod_banuser"]


def _loads_groups(statement):
    return "FROM groups" in statement and "groups_users" not in statement
