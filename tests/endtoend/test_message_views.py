import pytest
from werkzeug import exceptions
from flask_login import login_user

from flaskbb.message import views, models


def test_message_not_logged_in(application):
    """ check for redirect if not logged in """
    view = views.Inbox.as_view('inbox')
    with application.test_request_context():
        resp = view()
        assert resp.status != 302


def test_message_inbox(application, default_settings, conversation_msgs, user):
    view = views.Inbox()
    with application.test_request_context():
        login_user(user)
        resp = view.get()
        assert '<a href="/message/1/view">' in resp
        assert '<a href="/user/test_normal">test_normal</a>' in resp


def test_message_view_conversation(
        application, default_settings,
        conversation_msgs, user):
    with application.test_request_context():
        login_user(user)
        view = views.ViewConversation()
        resp = view.get(conversation_msgs.id)
        assert conversation_msgs.first_message.message in resp


def test_message_trash_restore_conversation(
        application, default_settings,
        conversation_msgs, user):
    move = views.MoveConversation()
    restore = views.RestoreConversation()
    with application.test_request_context():
        login_user(user)
        resp = move.post(conversation_msgs.id)
        assert resp.status != 302
        assert conversation_msgs.trash is True
        resp = restore.post(conversation_msgs.id)
        assert conversation_msgs.trash is False


def test_message_delete_conversation(
        application, default_settings,
        conversation_msgs, user):
    view = views.DeleteConversation()
    with application.test_request_context():
        login_user(user)
        resp = view.post(conversation_msgs.id)
        assert resp.status != 302


def test_message_trash(application, default_settings, user):
    # FIXME more sophisticated tests required
    view = views.TrashedMessages()
    with application.test_request_context():
        login_user(user)
        resp = view.get()
        assert 'No conversations found' in resp


def test_message_drafts(application, default_settings, user):
    # FIXME more sophisticated tests required
    view = views.DraftMessages()
    with application.test_request_context():
        login_user(user)
        resp = view.get()
        assert 'No conversations found' in resp


def test_message_sent(application, default_settings, user):
    # FIXME more sophisticated tests required
    view = views.SentMessages()
    with application.test_request_context():
        login_user(user)
        resp = view.get()
        assert 'No conversations found' in resp


def test_message_view_raw(
    application, conversation_msgs,
    default_settings, user, moderator_user):
    view = views.RawMessage()
    with application.test_request_context():
        login_user(user)
        resp = view.get(conversation_msgs.last_message.id)
        assert conversation_msgs.last_message.message in resp

        # same view should raise a 404 for a different user
        login_user(moderator_user)
        with pytest.raises(exceptions.NotFound):
            resp = view.get(conversation_msgs.last_message.id)
