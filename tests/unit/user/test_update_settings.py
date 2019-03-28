import pytest
from pluggy import HookimplMarker

from flaskbb.core.changesets import ChangeSetPostProcessor
from flaskbb.core.exceptions import PersistenceError
from flaskbb.core.user.update import SettingsUpdate
from flaskbb.user.models import User
from flaskbb.user.services.update import DefaultSettingsUpdateHandler


class TestDefaultSettingsUpdateHandler(object):
    def test_raises_persistence_error_if_save_fails(
        self, mocker, user, plugin_manager
    ):
        settings_update = SettingsUpdate(language="python", theme="molokai")
        db = mocker.Mock()
        db.session.commit.side_effect = Exception("no")
        hook_impl = mocker.Mock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        handler = DefaultSettingsUpdateHandler(
            db=db, plugin_manager=plugin_manager
        )

        with pytest.raises(PersistenceError) as excinfo:
            handler.apply_changeset(user, settings_update)

        assert "Could not update settings" in str(excinfo.value)
        hook_impl.post_process_changeset.assert_not_called()

    def test_actually_updates_password(
        self, user, database, mocker, plugin_manager
    ):
        settings_update = SettingsUpdate(language="python", theme="molokai")
        hook_impl = mocker.Mock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        handler = DefaultSettingsUpdateHandler(
            db=database, plugin_manager=plugin_manager
        )

        handler.apply_changeset(user, settings_update)
        same_user = User.query.get(user.id)

        assert same_user.theme == "molokai"
        assert same_user.language == "python"
        hook_impl.post_process_changeset.assert_called_once_with(
            user=user, settings_update=settings_update
        )

    @staticmethod
    def impl(post_processor):
        class Impl:
            @HookimplMarker("flaskbb")
            def flaskbb_settings_updated(self, user, settings_update):
                post_processor.post_process_changeset(
                    user=user, settings_update=settings_update
                )

        return Impl()
