from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time
from pytz import UTC

from flaskbb.auth.services import authentication as auth
from flaskbb.core.auth.authentication import StopAuthentication

pytestmark = pytest.mark.usefixtures('default_settings')


class TestBlockTooManyFailedLogins(object):
    provider = auth.BlockTooManyFailedLogins(
        auth.
        FailedLoginConfiguration(limit=1, lockout_window=timedelta(hours=1))
    )

    @freeze_time(datetime(2018, 1, 1, 13, 30))
    def test_raises_StopAuthentication_if_user_is_at_limit_and_inside_window(
            self, Fred
    ):
        Fred.last_failed_login = datetime(2018, 1, 1, 14, tzinfo=UTC)
        Fred.login_attempts = 1

        with pytest.raises(StopAuthentication) as excinfo:
            self.provider.authenticate(Fred.email, 'not considered')

        assert 'too many failed login attempts' in excinfo.value.reason

    @freeze_time(datetime(2018, 1, 1, 14))
    def test_doesnt_raise_if_user_is_at_limit_but_outside_window(self, Fred):
        Fred.last_failed_login = datetime(2018, 1, 1, 12, tzinfo=UTC)
        Fred.login_attempts = 1

        self.provider.authenticate(Fred.email, 'not considered')

    def test_doesnt_raise_if_user_is_below_limit_but_inside_window(self, Fred):
        Fred.last_failed_login = datetime(2018, 1, 1, 12, tzinfo=UTC)
        Fred.login_attempts = 0
        self.provider.authenticate(Fred.email, 'not considered')

    def test_handles_if_user_has_no_failed_login_attempts(self, Fred):
        Fred.login_attempts = 0
        Fred.last_failed_login = None

        self.provider.authenticate(Fred.email, 'not considered')

    def test_handles_if_user_doesnt_exist(self, Fred):
        self.provider.authenticate('completely@made.up', 'not considered')


class TestDefaultFlaskBBAuthProvider(object):
    provider = auth.DefaultFlaskBBAuthProvider()

    def test_returns_None_if_user_doesnt_exist(self, Fred):
        result = self.provider.authenticate('completely@made.up', 'lolnope')

        assert result is None

    def test_returns_None_if_password_doesnt_match(self, Fred):
        result = self.provider.authenticate(Fred.email, 'stillnotit')

        assert result is None

    def test_returns_user_if_identifer_and_password_match(self, Fred):
        result = self.provider.authenticate(Fred.email, 'fred')

        assert result.username == Fred.username


class TestMarkFailedLoginAttempt(object):
    handler = auth.MarkFailedLogin()

    @freeze_time(datetime(2018, 1, 1, 12))
    def test_increments_users_failed_logins_and_sets_last_fail_date(
            self, Fred
    ):
        Fred.login_attempts = 0
        Fred.last_failed_login = datetime.min.replace(tzinfo=UTC)
        self.handler.handle_authentication_failure(Fred.email)
        assert Fred.login_attempts == 1
        assert Fred.last_failed_login == datetime.now(UTC)

    def test_handles_if_user_doesnt_exist(self, Fred):
        self.handler.handle_authentication_failure('completely@made.up')


class TestClearFailedLogins(object):
    handler = auth.ClearFailedLogins()

    def test_clears_failed_logins_attempts(self, Fred):
        Fred.login_attempts = 1000
        self.handler.handle_post_auth(Fred)
        assert Fred.login_attempts == 0


class TestBlockUnactivatedUser(object):
    handler = auth.BlockUnactivatedUser()

    def test_raises_StopAuthentication_if_user_is_unactivated(
            self, unactivated_user
    ):
        with pytest.raises(StopAuthentication) as excinfo:
            self.handler.handle_post_auth(unactivated_user)

        assert 'In order to use your account' in excinfo.value.reason
