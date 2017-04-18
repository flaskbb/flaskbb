from flask_login import login_user

from flaskbb.message import views


def test_message_not_logged_in(application):
    """ check for redirect if not logged in """
    with application.test_request_context():
        resp = views.inbox()
        assert resp.status != 302


def test_message_inbox(application, default_settings, conversation_msgs, user):
    with application.test_request_context():
        login_user(user)
        resp = views.inbox()
        print resp
        assert 'From <a href="/user/test_normal">test_normal</a>' in resp


def test_message_view_conversation(
        application, default_settings,
        conversation_msgs, user):
    with application.test_request_context():
        login_user(user)
        resp = views.view_conversation(conversation_msgs.id)
        assert conversation_msgs.first_message.message in resp


def test_message_trash_restore_conversation(
        application, default_settings,
        conversation_msgs, user):
    with application.test_request_context():
        login_user(user)
        resp = views.move_conversation(conversation_msgs.id)
        assert resp.status != 302
        assert conversation_msgs.trash is True
        resp = views.restore_conversation(conversation_msgs.id)
        assert conversation_msgs.trash is False


def test_message_delete_conversation(
        application, default_settings,
        conversation_msgs, user):
    with application.test_request_context():
        login_user(user)
        resp = views.delete_conversation(conversation_msgs.id)
        assert resp.status != 302


def test_message_trash(application, default_settings, user):
    # FIXME more sophisticated tests required
    with application.test_request_context():
        login_user(user)
        resp = views.trash()
        assert 'No conversations found' in resp


def test_message_drafts(application, default_settings, user):
    # FIXME more sophisticated tests required
    with application.test_request_context():
        login_user(user)
        resp = views.drafts()
        assert 'No conversations found' in resp


def test_message_sent(application, default_settings, user):
    # FIXME more sophisticated tests required
    with application.test_request_context():
        login_user(user)
        resp = views.sent()
        assert 'No conversations found' in resp
