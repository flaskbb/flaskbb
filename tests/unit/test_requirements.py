from flaskbb.utils import requirements as r
from flaskbb.utils.datastructures import SimpleNamespace


def test_Fred_IsNotAdmin(Fred):
    assert not r.IsAdmin(Fred, None)


def test_IsAdmin_with_admin(admin_user):
    assert r.IsAdmin(admin_user, None)


def test_IsAtleastModerator_with_mod(moderator_user):
    assert r.IsAtleastModerator(moderator_user, None)


def test_IsAtleastModerator_with_supermod(super_moderator_user):
    assert r.IsAtleastModerator(super_moderator_user, None)


def test_IsAtleastModerator_with_admin(admin_user):
    assert r.IsAtleastModerator(admin_user, None)


def test_IsAtleastSuperModerator_with_not_smod(moderator_user):
    assert not r.IsAtleastSuperModerator(moderator_user, None)


def test_CanBanUser_with_admin(admin_user):
    assert r.CanBanUser(admin_user, None)


def test_CanBanUser_with_smod(super_moderator_user):
    assert r.CanBanUser(super_moderator_user, None)


def test_CanBanUser_with_mod(moderator_user):
    assert r.CanBanUser(moderator_user, None)


def test_Fred_CannotBanUser(Fred):
    assert not r.CanBanUser(Fred, None)


def test_CanEditTopic_with_member(user, topic):
    request = SimpleNamespace(view_args={'topic_id': topic.id})
    assert r.CanEditPost(user, request)


def test_Fred_cannot_edit_other_members_post(user, Fred, topic):
    request = SimpleNamespace(view_args={'topic_id': topic.id})
    assert not r.CanEditPost(Fred, request)


def test_Fred_CannotEditLockedTopic(Fred, topic_locked):
    request = SimpleNamespace(view_args={'topic_id': topic_locked.id})
    assert not r.CanEditPost(Fred, request)


def test_Moderator_in_Forum_CanEditLockedTopic(moderator_user, topic_locked):
    request = SimpleNamespace(view_args={'topic_id': topic_locked.id})
    assert r.CanEditPost(moderator_user, request)


def test_FredIsAMod_but_still_cant_edit_topic_in_locked_forum(Fred, topic_locked, default_groups):
    request = SimpleNamespace(view_args={'topic_id': topic_locked.id})
    Fred.primary_group = default_groups[2]
    assert not r.CanEditPost(Fred, request)


def test_Fred_cannot_reply_to_locked_topic(Fred, topic_locked):
    request = SimpleNamespace(view_args={'topic_id': topic_locked.id})
    assert not r.CanPostReply(Fred, request)


def test_Fred_cannot_delete_others_post(Fred, topic):
    request = SimpleNamespace(view_args={'post_id': topic.first_post.id})
    assert not r.CanDeletePost(Fred, request)


def test_Mod_can_delete_others_post(moderator_user, topic):
    request = SimpleNamespace(view_args={'post_id': topic.first_post.id})
    assert r.CanDeletePost(moderator_user, request)
