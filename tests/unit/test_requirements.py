from flaskbb.utils import requirements as r
from flaskbb.utils.datastructures import SimpleNamespace
from flaskbb.user.models import User


def test_Fred_IsNotAdmin(Fred):
    assert not r.IsAdmin().fulfill(Fred, None)


def test_IsAdmin_with_admin(admin_user):
    assert r.IsAdmin().fulfill(admin_user, None)


def test_IsAtleastModerator_with_mod(moderator_user):
    assert r.IsAtleastModerator.fulfill(moderator_user, None)


def test_IsAtleastModerator_with_supermod(super_moderator_user):
    assert r.IsAtleastModerator.fulfill(super_moderator_user, None)


def test_IsAtleastModerator_with_admin(admin_user):
    assert r.IsAtleastModerator.fulfill(admin_user, None)


def test_IsAtleastSuperModerator_with_not_smod(moderator_user):
    assert not r.IsAtleastSuperModerator.fulfill(moderator_user, None)


def test_CanBanUser_with_admin(admin_user):
    assert r.CanBanUser.fulfill(admin_user, None)


def test_CanBanUser_with_smod(super_moderator_user):
    assert r.CanBanUser.fulfill(super_moderator_user, None)


def test_CanBanUser_with_mod(moderator_user):
    assert r.CanBanUser.fulfill(moderator_user, None)


def test_Fred_CannotBanUser(Fred):
    assert not r.CanBanUser.fulfill(Fred, None)


def test_CanEditTopic_with_member(user, topic):
    request = SimpleNamespace(view_args={'topic_id': topic.id})
    assert r.CanEditPost.fulfill(user, request)


def test_Fred_cannot_edit_other_members_post(user, Fred, topic):
    request = SimpleNamespace(view_args={'topic_id': topic.id})
    assert not r.CanEditPost(Fred, request)


def test_Fred_CannotEditLockedTopic(Fred, topic_locked):
    request = SimpleNamespace(view_args={'topic_id': topic_locked.id})
    assert not r.CanEditPost.fulfill(Fred, request)


def test_Moderator_in_Forum_CanEditLockedTopic(moderator_user, topic_locked):
    request = SimpleNamespace(view_args={'topic_id': topic_locked.id})
    assert r.CanEditPost.fulfill(moderator_user, request)


def test_FredIsAMod_but_still_cant_edit_topic_in_locked_forum(Fred, topic_locked, default_groups):
    request = SimpleNamespace(view_args={'topic_id': topic_locked.id})
    Fred.primary_group = default_groups[2]
    assert not r.CanEditPost.fulfill(Fred, request)


def test_Fred_cannot_reply_to_locked_topic(Fred, topic_locked):
    request = SimpleNamespace(view_args={'topic_id': topic_locked.id})
    assert not r.CanPostReply.fulfill(Fred, request)


def test_Fred_cannot_delete_others_post(Fred, topic):
    request = SimpleNamespace(view_args={'post_id': topic.first_post.id})
    assert not r.CanDeletePost.fulfill(Fred, request)


def test_Mod_can_delete_others_post(moderator_user, topic):
    request = SimpleNamespace(view_args={'post_id': topic.first_post.id})
    assert r.CanDeletePost.fulfill(moderator_user, request)
