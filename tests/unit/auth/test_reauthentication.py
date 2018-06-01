from datetime import datetime

import pytest
from flaskbb.auth.services import reauthentication as reauth
from flaskbb.core.auth.authentication import (PostReauthenticateHandler,
                                              ReauthenticateFailureHandler,
                                              ReauthenticateProvider,
                                              StopAuthentication)
from freezegun import freeze_time
from pluggy import HookimplMarker
from pytz import UTC

pytestmark = pytest.mark.usefixtures('default_settings')


def test_default_reauth_returns_true_if_secret_matches_user(Fred):
    service = reauth.DefaultFlaskBBReauthProvider()

    assert service.reauthenticate(Fred, 'fred')


def test_clears_failed_logins_attempts(Fred):
    service = reauth.ClearFailedLoginsOnReauth()
    Fred.login_attempts = 1000
    service.handle_post_reauth(Fred)
    assert Fred.login_attempts == 0


@freeze_time(datetime(2018, 1, 1, 13, 30))
def test_marks_failed_login_attempt(Fred):
    service = reauth.MarkFailedReauth()
    Fred.login_attempts = 1
    Fred.last_failed_login = datetime.min.replace(tzinfo=UTC)

    service.handle_reauth_failure(Fred)

    assert Fred.login_attempts == 2
    assert Fred.last_failed_login == datetime(2018, 1, 1, 13, 30, tzinfo=UTC)


class TestPluginAuthenticationManager(object):

    def raises_stop_authentication_if_user_isnt_reauthenticated(
            self, plugin_manager, mocker, database, Fred
    ):
        service = self._get_auth_manager(plugin_manager, database)
        reauth = mocker.MagicMock(spec=ReauthenticateProvider)
        plugin_manager.register(self.impls(reauth=reauth))

        with pytest.raises(StopAuthentication) as excinfo:
            service.reauthenticate(Fred, 'nope')

        reauth.assert_called_once_with(user=Fred, secret='nope')
        assert excinfo.value.reason == "Wrong password."

    def test_runs_failed_hooks_when_stopauthentication_is_raised(
            self, plugin_manager, mocker, database, Fred
    ):
        service = self._get_auth_manager(plugin_manager, database)
        failure = mocker.MagicMock(spec=ReauthenticateFailureHandler)
        plugin_manager.register(self.impls(failure=failure))

        with pytest.raises(StopAuthentication):
            service.reauthenticate(Fred, 'nope')

        failure.assert_called_once_with(user=Fred)

    def test_runs_post_reauth_handler_if_user_authenticates(
            self, plugin_manager, mocker, Fred, database
    ):
        service = self._get_auth_manager(plugin_manager, database)
        reauth = mocker.MagicMock(
            spec=ReauthenticateProvider, return_value=Fred
        )
        post_reauth = mocker.MagicMock(spec=PostReauthenticateHandler)
        plugin_manager.register(
            self.impls(reauth=reauth, post_reauth=post_reauth)
        )

        service.reauthenticate(Fred, 'fred')

        reauth.assert_called_once_with(user=Fred, secret='fred')
        post_reauth.assert_called_once_with(user=Fred)

    def test_reraises_if_session_commit_fails(
            self, mocker, plugin_manager, Fred
    ):

        class NotAnActualException(Exception):
            pass

        db = mocker.Mock()
        db.session.commit.side_effect = NotAnActualException
        service = self._get_auth_manager(plugin_manager, db)

        with pytest.raises(NotAnActualException):
            service.reauthenticate('doesnt exist', 'nope')

        db.session.rollback.assert_called_once_with()

    def _get_auth_manager(self, plugin_manager, db):
        return reauth.PluginReauthenticationManager(
            plugin_manager, session=db.session
        )

    @staticmethod
    def impls(reauth=None, post_reauth=None, failure=None):
        impl = HookimplMarker('flaskbb')

        class Impls:
            if reauth is not None:

                @impl
                def flaskbb_reauth_attempt(self, user, secret):
                    return reauth(user=user, secret=secret)

            if post_reauth is not None:

                @impl
                def flaskbb_post_reauth(self, user):
                    post_reauth(user=user)

            if failure is not None:

                @impl
                def flaskbb_reauth_failed(self, user):
                    failure(user=user)

        return Impls()
