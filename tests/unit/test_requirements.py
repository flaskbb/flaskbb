import pytest
from flask import g
from flaskbb.utils import requirements as r


def push_onto_request_context(**kw):
    for name, value in kw.items():
        setattr(g, name, value)


@pytest.fixture
def request_context(application):
    with application.test_request_context():
        yield


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


def test_CanEditTopic_with_member(user, topic, request_context):
    push_onto_request_context(topic=topic)
    assert r.CanEditPost(user)


def test_Fred_cannot_edit_other_members_post(user, Fred, topic, request_context):
    push_onto_request_context(topic=topic)
    assert not r.CanEditPost(Fred)


def test_Fred_CannotEditLockedTopic(Fred, topic_locked, request_context):
    push_onto_request_context(topic=topic_locked)
    assert not r.CanEditPost(Fred)


def test_Moderator_in_Forum_CanEditLockedTopic(
    moderator_user, topic_locked, request_context
):
    push_onto_request_context(topic=topic_locked)
    assert r.CanEditPost(moderator_user)


def test_FredIsAMod_but_still_cant_edit_topic_in_locked_forum(
    Fred, topic_locked, default_groups, request_context
):
    Fred.primary_group = default_groups[2]

    push_onto_request_context(topic=topic_locked)
    assert not r.CanEditPost(Fred)


def test_Fred_cannot_reply_to_locked_topic(Fred, topic_locked, request_context):
    push_onto_request_context(topic=topic_locked)
    assert not r.CanPostReply(Fred)


def test_Fred_cannot_delete_others_post(Fred, topic, request_context):
    push_onto_request_context(post=topic.first_post)
    assert not r.CanDeletePost(Fred)


def test_Mod_can_delete_others_post(moderator_user, topic, request_context):
    push_onto_request_context(post=topic.first_post)
    assert r.CanDeletePost(moderator_user)


def test_CanPostAttachment_with_member(user):
    assert r.CanPostAttachment(user)


def test_CanPostAttachment_with_mod(moderator_user):
    assert r.CanPostAttachment(moderator_user)


def test_guest_cannot_post_attachment(guest, forum, request_context):
    push_onto_request_context(forum=forum)
    assert not r.CanPostAttachment(guest)


def test_IsMorePrivilegedThan_ranks_admin_over_mod(admin_user, moderator_user):
    assert r.IsMorePrivilegedThan(moderator_user)(admin_user)


def test_member_can_post_topic_in_unlocked_forum(user, forum, request_context):
    push_onto_request_context(forum=forum, topic=None, post=None)
    assert r.CanPostTopic(user)


def test_member_cannot_post_topic_in_locked_forum(user, forum_locked, request_context):
    push_onto_request_context(forum=forum_locked, topic=None, post=None)
    assert not r.CanPostTopic(user)


def test_IsMorePrivilegedThan_ranks_mod_over_member(moderator_user, user):
    assert r.IsMorePrivilegedThan(user)(moderator_user)


def test_IsMorePrivilegedThan_is_strict_between_equals(
    moderator_user, other_moderator_user
):
    assert not r.IsMorePrivilegedThan(other_moderator_user)(moderator_user)


def test_IsMorePrivilegedThan_is_false_for_self(moderator_user):
    assert not r.IsMorePrivilegedThan(moderator_user)(moderator_user)


def test_IsMorePrivilegedThan_counts_secondary_groups(
    user, moderator_user, default_groups
):
    """A privileged secondary group must outrank the primary group alone."""
    user.save(groups=[default_groups[0]])
    assert not r.IsMorePrivilegedThan(user)(moderator_user)


def test_CanEditTargetUser_mod_can_edit_member(moderator_user, user):
    assert r.CanEditTargetUser(user)(moderator_user)


def test_CanEditTargetUser_mod_cannot_edit_other_mod(
    moderator_user, other_moderator_user
):
    assert not r.CanEditTargetUser(other_moderator_user)(moderator_user)


def test_CanEditTargetUser_mod_cannot_edit_supermod(
    moderator_user, super_moderator_user
):
    assert not r.CanEditTargetUser(super_moderator_user)(moderator_user)


def test_CanEditTargetUser_mod_cannot_edit_admin(moderator_user, admin_user):
    assert not r.CanEditTargetUser(admin_user)(moderator_user)


def test_CanEditTargetUser_admin_can_edit_admin(admin_user, super_moderator_user):
    """Admins bypass the ranking check so they can still manage each other."""
    assert r.CanEditTargetUser(admin_user)(admin_user)
    assert r.CanEditTargetUser(super_moderator_user)(admin_user)


def test_CanEditTargetUser_still_requires_the_permission(Fred, user):
    assert not r.CanEditTargetUser(user)(Fred)


def test_CanBanTargetUser_mod_cannot_ban_supermod(moderator_user, super_moderator_user):
    assert not r.CanBanTargetUser(super_moderator_user)(moderator_user)


def test_CanBanTargetUser_mod_can_ban_member(moderator_user, user):
    assert r.CanBanTargetUser(user)(moderator_user)
