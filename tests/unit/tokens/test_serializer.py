from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from flaskbb import tokens
from flaskbb.core.tokens import Token, TokenActions, TokenError

pytestmark = pytest.mark.usefixtures('default_settings')


def test_can_round_trip_token():
    serializer = tokens.FlaskBBTokenSerializer(
        'hello i am secret', timedelta(seconds=100)
    )
    token = Token(user_id=1, operation=TokenActions.RESET_PASSWORD)
    roundtrip = serializer.loads(serializer.dumps(token))

    assert token == roundtrip


def test_raises_token_error_with_bad_data():
    serializer = tokens.FlaskBBTokenSerializer(
        'hello i am also secret', timedelta(seconds=100)
    )

    with pytest.raises(TokenError) as excinfo:
        serializer.loads('not actually a token')
    assert 'invalid' in str(excinfo.value)


def test_expired_token_raises():
    serializer = tokens.FlaskBBTokenSerializer(
        'i am a secret not', expiry=timedelta(seconds=1)
    )
    dumped_token = serializer.dumps(
        Token(user_id=1, operation=TokenActions.RESET_PASSWORD)
    )

    with freeze_time(datetime.now() + timedelta(days=10)):
        with pytest.raises(TokenError) as excinfo:
            serializer.loads(dumped_token)

    assert 'expired' in str(excinfo.value)
