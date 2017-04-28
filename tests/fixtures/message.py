import pytest
import uuid
from flaskbb.message.models import Conversation, Message


@pytest.fixture
def conversation(database, user, admin_user):
    conversation = Conversation(
        user_id=user.id,
        from_user_id=user.id,
        to_user_id=admin_user.id,
        shared_id=uuid.uuid4()
    )
    conversation.save()
    return conversation


@pytest.fixture
def conversation_msgs(conversation, user, admin_user):
    message = Message(
        user_id=user.id,
        conversation_id=conversation.id,
        message="First message"
    )
    conversation.save(message=message)
    message = Message(
        user_id=admin_user.id,
        conversation_id=conversation.id,
        message="Second message"
    )
    conversation.save(message=message)
    return conversation
