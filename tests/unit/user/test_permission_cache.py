"""The permissions of an identity are snapshotted once per request. Groups
and their permissions are cached across requests under a version every group
change bumps; membership is read once per request for every loaded user.
"""

from flask_login import login_user, logout_user
from flaskbb.extensions import cache, db
from flaskbb.permissions import current_permissions, permission_manager, PermissionLevel
from flaskbb.user.models import Group, GroupRole, permissions_version, User
from flaskbb.utils import requirements as r

ADMINISTRATOR, SUPER_MODERATOR, MODERATOR, MEMBER, BANNED, GUEST = range(6)


def next_request():
    """The test client shares the test's app context, so ``g`` has to be
    reset by hand to behave like a new request.
    """
    permission_manager.forget()


def test_permissions_are_snapshotted_once_per_request(user):
    assert permission_manager.for_user(user) is permission_manager.for_user(user)
    assert user.permissions is permission_manager.for_user(user)


def test_guests_share_one_snapshot(guest, default_groups):
    assert permission_manager.for_user(guest) is permission_manager.for_user(guest)
    assert not guest.permissions["posttopic"]


def test_invalidating_a_user_forgets_the_snapshot(user):
    stale = permission_manager.for_user(user)
    user.invalidate_cache()
    assert permission_manager.for_user(user) is not stale


def test_forgetting_rebuilds_the_permissions(user):
    stale = permission_manager.for_user(user)
    permission_manager.forget()
    assert permission_manager.for_user(user) is not stale


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
    permissions = permission_manager.for_user(moderator_user)
    assert permissions.moderates(forum)

    forum.moderators = []
    forum.save()

    assert permissions.moderates(forum)
    permission_manager.forget()
    assert not permission_manager.for_user(moderator_user).moderates(forum)


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
    assert permission_manager.for_user(user).group_ids
    next_request()
    selects.clear()

    assert user.permissions["postreply"]
    assert not r.IsAdmin(user)
    assert permission_manager.for_user(user).group_ids

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
    permission_manager.forget()
    selects.clear()

    assert user.permissions["mod_banuser"]

    assert sum("FROM group_permissions" in statement for statement in selects) == 1


def test_cold_guest_permissions_need_no_membership_query(guest, default_groups, selects):
    cache.clear()
    permission_manager.forget()
    selects.clear()

    assert not guest.permissions["postreply"]

    assert not any("FROM groups_users" in statement for statement in selects)


def test_group_tables_are_loaded_once_for_every_identity(user, moderator_user, guest, selects):
    cache.clear()
    permission_manager.forget()
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
    permission_manager.forget()
    selects.clear()

    assert r.can_ban_user(user)(super_moderator_user)
    assert r.can_ban_user(moderator_user)(super_moderator_user)
    assert not r.can_ban_user(admin_user)(super_moderator_user)
    assert not r.can_ban_user(super_moderator_user)(moderator_user)
    assert permission_manager.for_user(user).rank == GroupRole.MODERATOR.rank
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


def test_permissions_are_a_mapping(user):
    permissions = permission_manager.for_user(user)

    assert "postreply" in permissions
    assert "flyaround" not in permissions
    assert permissions["postreply"] is True
    assert permissions.get("flyaround") is None
    assert not permissions.has("flyaround")
    assert set(permissions) == set(user.get_permissions())
    assert len(permissions) == len(user.get_permissions())


def test_current_permissions_follow_the_logged_in_user(application, user, admin_user):
    with application.test_request_context():
        login_user(user)
        assert current_permissions.rank == GroupRole.MEMBER.rank
        assert not current_permissions.has("mod_banuser")
        logout_user()

        login_user(admin_user)
        assert current_permissions.rank == GroupRole.ADMINISTRATOR.rank
        assert current_permissions["mod_banuser"]
        logout_user()

        assert not current_permissions.is_authenticated
        assert not current_permissions.has("postreply")


def test_never_wins_over_a_group_that_allows(user, default_groups):
    user.save(groups=[default_groups[MODERATOR]])
    assert user.permissions["deletepost"]

    default_groups[MEMBER].set_permission("deletepost", PermissionLevel.NEVER)
    default_groups[MEMBER].save()

    assert not user.permissions["deletepost"]
    assert not r.Has("deletepost")(user)


def test_deny_leaves_the_decision_to_the_other_groups(user, default_groups):
    user.save(groups=[default_groups[MODERATOR]])
    default_groups[MEMBER].set_permission("deletepost", PermissionLevel.DENY)
    default_groups[MEMBER].save()

    assert user.permissions["deletepost"]


def test_an_undecided_permission_counts_as_its_default(user, default_groups):
    member = default_groups[MEMBER]
    member.permission_rows = [row for row in member.permission_rows if row.permission != "editpost"]
    member.save()

    assert member.permission_levels["editpost"] is PermissionLevel.ALLOW
    assert user.permissions["editpost"]
