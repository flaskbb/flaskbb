import pytest
from flask import _request_ctx_stack, request

from flaskbb.utils import requirements as r


def push_onto_request_context(**kw):
    for name, value in kw.items():
        setattr(_request_ctx_stack.top, name, value)


@pytest.yield_fixture
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


def test_Fred_cannot_edit_other_members_post(user, Fred, topic,
                                             request_context):
    push_onto_request_context(topic=topic)
    assert not r.CanEditPost(Fred)


def test_Fred_CannotEditLockedTopic(Fred, topic_locked, request_context):
    push_onto_request_context(topic=topic_locked)
    assert not r.CanEditPost(Fred)


def test_Moderator_in_Forum_CanEditLockedTopic(moderator_user, topic_locked,
                                               request_context):
    push_onto_request_context(topic=topic_locked)
    assert r.CanEditPost(moderator_user)


def test_FredIsAMod_but_still_cant_edit_topic_in_locked_forum(
        Fred, topic_locked, default_groups, request_context):

    Fred.primary_group = default_groups[2]

    push_onto_request_context(topic=topic_locked)
    assert not r.CanEditPost(Fred)


def test_Fred_cannot_reply_to_locked_topic(Fred, topic_locked,
                                           request_context):
    push_onto_request_context(topic=topic_locked)
    assert not r.CanPostReply(Fred)


def test_Fred_cannot_delete_others_post(Fred, topic, request_context):
    push_onto_request_context(post=topic.first_post)
    assert not r.CanDeletePost(Fred)


def test_Mod_can_delete_others_post(moderator_user, topic, request_context):
    push_onto_request_context(post=topic.first_post)
    assert r.CanDeletePost(moderator_user)
