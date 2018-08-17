from uuid import uuid4

import pytest
from pluggy import HookimplMarker

from flaskbb.core.changesets import ChangeSetValidator, ChangeSetPostProcessor
from flaskbb.core.exceptions import PersistenceError, StopValidation, ValidationError
from flaskbb.core.user.update import (
    PasswordUpdate,
)
from flaskbb.user.models import User
from flaskbb.user.services.update import DefaultPasswordUpdateHandler


class TestDefaultPasswordUpdateHandler(object):
    def test_raises_stop_validation_if_errors_occur(
        self, mock, user, database, plugin_manager
    ):
        validator = mock.Mock(spec=ChangeSetValidator)
        validator.validate.side_effect = ValidationError(
            "new_password", "Don't use that password"
        )
        password_change = PasswordUpdate(str(uuid4()), str(uuid4()))
        hook_impl = mock.MagicMock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        handler = DefaultPasswordUpdateHandler(
            db=database, plugin_manager=plugin_manager, validators=[validator]
        )

        with pytest.raises(StopValidation) as excinfo:
            handler.apply_changeset(user, password_change)
        assert excinfo.value.reasons == [("new_password", "Don't use that password")]
        hook_impl.post_process_changeset.assert_not_called()

    def test_raises_persistence_error_if_save_fails(self, mock, user, plugin_manager):
        password_change = PasswordUpdate(str(uuid4()), str(uuid4()))
        db = mock.Mock()
        db.session.commit.side_effect = Exception("no")
        hook_impl = mock.MagicMock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        handler = DefaultPasswordUpdateHandler(
            db=db, plugin_manager=plugin_manager, validators=[]
        )

        with pytest.raises(PersistenceError) as excinfo:
            handler.apply_changeset(user, password_change)

        assert "Could not update password" in str(excinfo.value)
        hook_impl.post_process_changeset.assert_not_called()

    def test_actually_updates_password(self, user, database, plugin_manager, mock):
        new_password = str(uuid4())
        password_change = PasswordUpdate("test", new_password)
        hook_impl = mock.MagicMock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        handler = DefaultPasswordUpdateHandler(
            db=database, plugin_manager=plugin_manager, validators=[]
        )

        handler.apply_changeset(user, password_change)
        same_user = User.query.get(user.id)

        assert same_user.check_password(new_password)
        hook_impl.post_process_changeset.assert_called_once_with(user=user)

    @staticmethod
    def impl(post_processor):
        class Impl:
            @HookimplMarker("flaskbb")
            def flaskbb_password_updated(self, user):
                post_processor.post_process_changeset(user=user)

        return Impl()
