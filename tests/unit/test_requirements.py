import pytest
from flask import g
from flaskbb.exceptions import FlaskBBError
from flaskbb.utils import requirements as r


@pytest.fixture
def request_topic_on_g(application, topic):
    with application.test_request_context():
        g.topic = topic
        try:
            yield topic
        finally:
            g.pop("topic", None)


def test_Fred_IsNotAdmin(Fred):
    assert not r.IsAdmin(Fred)


def test_IsAdmin_with_admin(admin_user):
    assert r.IsAdmin(admin_user)


def test_IsAtleastModerator_with_mod(moderator_user):
    assert r.IsAtleastModerator(moderator_user)


def test_IsAtleastModerator_with_supermod(super_moderator_user):
    assert r.IsAtleastModerator(super_moderator_user)


def test_IsAtleastModerator_with_admin(admin_user):
    assert r.IsAtleastModerator(admin_user)


def test_IsAtleastSuperModerator_with_not_smod(moderator_user):
    assert not r.IsAtleastSuperModerator(moderator_user)


def test_CanBanUser_with_admin(admin_user):
    assert r.CanBanUser(admin_user)


def test_CanBanUser_with_smod(super_moderator_user):
    assert r.CanBanUser(super_moderator_user)


def test_CanBanUser_with_mod(moderator_user):
    assert r.CanBanUser(moderator_user)


def test_Fred_CannotBanUser(Fred):
    assert not r.CanBanUser(Fred)


def test_member_can_edit_own_post(user, topic):
    assert r.can_edit_post(topic.first_post)(user)


def test_Fred_cannot_edit_other_members_post(Fred, topic):
    assert not r.can_edit_post(topic.first_post)(Fred)


def test_member_cannot_edit_post_in_locked_topic(user, topic_locked):
    assert not r.can_edit_post(topic_locked.first_post)(user)


def test_moderator_in_forum_can_edit_post_in_locked_topic(moderator_user, topic_locked):
    assert r.can_edit_post(topic_locked.first_post)(moderator_user)


def test_moderator_of_other_forums_cannot_edit_post_in_locked_topic(
    other_moderator_user, topic_locked
):
    assert not r.can_edit_post(topic_locked.first_post)(other_moderator_user)


def test_member_can_edit_own_topic(user, topic):
    assert r.can_edit_topic(topic)(user)


def test_member_cannot_edit_topic_in_locked_forum(user, topic_in_locked_forum):
    assert not r.can_edit_topic(topic_in_locked_forum)(user)


def test_admin_can_edit_topic_in_locked_forum(admin_user, topic_in_locked_forum):
    assert r.can_edit_topic(topic_in_locked_forum)(admin_user)


def test_member_can_reply(user, topic):
    assert r.can_post_reply(topic)(user)


def test_Fred_cannot_reply_to_locked_topic(Fred, topic_locked):
    assert not r.can_post_reply(topic_locked)(Fred)


def test_moderator_in_forum_can_reply_to_locked_topic(moderator_user, topic_locked):
    assert r.can_post_reply(topic_locked)(moderator_user)


def test_Fred_cannot_delete_others_post(Fred, topic):
    assert not r.can_delete_post(topic.first_post)(Fred)


def test_Mod_can_delete_others_post(moderator_user, topic):
    assert r.can_delete_post(topic.first_post)(moderator_user)


def test_member_cannot_delete_own_topic_without_permission(user, topic):
    assert not r.can_delete_topic(topic)(user)


def test_Mod_can_delete_others_topic(moderator_user, topic):
    assert r.can_delete_topic(topic)(moderator_user)


def test_member_can_post_attachment(user, forum):
    assert r.can_post_attachment(forum)(user)


def test_moderator_can_post_attachment(moderator_user, forum):
    assert r.can_post_attachment(forum)(moderator_user)


def test_guest_cannot_post_attachment(guest, forum):
    assert not r.can_post_attachment(forum)(guest)


def test_member_can_post_topic_in_unlocked_forum(user, forum):
    assert r.can_post_topic(forum)(user)


def test_member_cannot_post_topic_in_locked_forum(user, forum_locked):
    assert not r.can_post_topic(forum_locked)(user)


def test_admin_can_post_topic_in_locked_forum(admin_user, forum_locked):
    assert r.can_post_topic(forum_locked)(admin_user)


def test_super_moderator_cannot_post_topic_in_locked_forum(super_moderator_user, forum_locked):
    assert not r.can_post_topic(forum_locked)(super_moderator_user)


def test_member_cannot_access_forum_closed_to_their_groups(user, admin_user, forum, default_groups):
    forum.groups = [default_groups[0]]
    forum.save()

    assert not r.can_access_forum(forum)(user)
    assert r.can_access_forum(forum)(admin_user)


def test_moderator_moderates_only_their_own_forum(moderator_user, other_moderator_user, forum):
    assert r.can_moderate(forum)(moderator_user)
    assert not r.can_moderate(forum)(other_moderator_user)


def test_super_moderator_moderates_every_forum(super_moderator_user, forum):
    assert r.can_moderate(forum)(super_moderator_user)


def test_ForRequest_applies_the_policy_to_the_object_of_the_request(user, request_topic_on_g):
    assert r.ForRequest(r.can_post_reply, r.request_topic)(user)


def test_ForRequest_denies_like_the_policy_it_wraps(Fred, request_topic_on_g):
    request_topic_on_g.locked = True
    assert not r.ForRequest(r.can_post_reply, r.request_topic)(Fred)


def test_request_forum_without_a_forum_in_the_request_raises(application):
    for name in ("post", "topic", "forum"):
        g.pop(name, None)
    with application.test_request_context():
        with pytest.raises(FlaskBBError):
            r.request_forum()


def test_IsMorePrivilegedThan_ranks_admin_over_mod(admin_user, moderator_user):
    assert r.IsMorePrivilegedThan(moderator_user)(admin_user)


def test_IsMorePrivilegedThan_ranks_mod_over_member(moderator_user, user):
    assert r.IsMorePrivilegedThan(user)(moderator_user)


def test_IsMorePrivilegedThan_is_strict_between_equals(moderator_user, other_moderator_user):
    assert not r.IsMorePrivilegedThan(other_moderator_user)(moderator_user)


def test_IsMorePrivilegedThan_is_false_for_self(moderator_user):
    assert not r.IsMorePrivilegedThan(moderator_user)(moderator_user)


def test_IsMorePrivilegedThan_counts_secondary_groups(user, moderator_user, default_groups):
    """A privileged secondary group must outrank the primary group alone."""
    user.save(groups=[default_groups[0]])
    assert not r.IsMorePrivilegedThan(user)(moderator_user)


def test_can_edit_user_mod_can_edit_member(moderator_user, user):
    assert r.can_edit_user(user)(moderator_user)


def test_can_edit_user_mod_cannot_edit_other_mod(moderator_user, other_moderator_user):
    assert not r.can_edit_user(other_moderator_user)(moderator_user)


def test_can_edit_user_mod_cannot_edit_supermod(moderator_user, super_moderator_user):
    assert not r.can_edit_user(super_moderator_user)(moderator_user)


def test_can_edit_user_mod_cannot_edit_admin(moderator_user, admin_user):
    assert not r.can_edit_user(admin_user)(moderator_user)


def test_can_edit_user_admin_can_edit_admin(admin_user, super_moderator_user):
    """Admins bypass the ranking check so they can still manage each other."""
    assert r.can_edit_user(admin_user)(admin_user)
    assert r.can_edit_user(super_moderator_user)(admin_user)


def test_can_edit_user_still_requires_the_permission(Fred, user):
    assert not r.can_edit_user(user)(Fred)


def test_can_edit_user_without_a_target_is_the_plain_permission(moderator_user, Fred):
    assert r.can_edit_user()(moderator_user)
    assert not r.can_edit_user()(Fred)


def test_can_ban_user_mod_cannot_ban_supermod(moderator_user, super_moderator_user):
    assert not r.can_ban_user(super_moderator_user)(moderator_user)


def test_can_ban_user_mod_can_ban_member(moderator_user, user):
    assert r.can_ban_user(user)(moderator_user)
