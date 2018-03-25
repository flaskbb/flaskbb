import json

import pytest

from flaskbb.core.tokens import Token


class SimpleTokenSerializer:

    @staticmethod
    def dumps(token):
        return json.dumps({'user_id': token.user_id, 'op': token.operation})

    @staticmethod
    def loads(raw_token):
        loaded = json.loads(raw_token)
        return Token(user_id=loaded['user_id'], operation=loaded['op'])


@pytest.fixture(scope='session')
def token_serializer():
    return SimpleTokenSerializer
