from uuid import uuid4

import pytest
from pluggy import HookimplMarker

from flaskbb.core.changesets import ChangeSetPostProcessor, ChangeSetValidator
from flaskbb.core.exceptions import (PersistenceError, StopValidation,
                                     ValidationError)
from flaskbb.core.user.update import UserDetailsChange
from flaskbb.user.models import User
from flaskbb.user.services.update import DefaultDetailsUpdateHandler


class TestDefaultDetailsUpdateHandler(object):
    def test_raises_stop_validation_if_errors_occur(
        self, mocker, user, database, plugin_manager
    ):
        validator = mocker.Mock(spec=ChangeSetValidator)
        validator.validate.side_effect = ValidationError(
            "location", "Dont be from there"
        )

        details = UserDetailsChange()
        hook_impl = mocker.Mock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        handler = DefaultDetailsUpdateHandler(
            validators=[validator], db=database, plugin_manager=plugin_manager
        )

        with pytest.raises(StopValidation) as excinfo:
            handler.apply_changeset(user, details)

        assert excinfo.value.reasons == [("location", "Dont be from there")]
        hook_impl.post_process_changeset.assert_not_called()

    def test_raises_persistence_error_if_save_fails(
        self, mocker, user, plugin_manager
    ):
        details = UserDetailsChange()
        db = mocker.Mock()
        db.session.commit.side_effect = Exception("no")

        hook_impl = mocker.Mock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        handler = DefaultDetailsUpdateHandler(
            validators=[], db=db, plugin_manager=plugin_manager
        )

        with pytest.raises(PersistenceError) as excinfo:
            handler.apply_changeset(user, details)

        assert "Could not update details" in str(excinfo.value)
        hook_impl.post_process_changeset.assert_not_called()

    def test_actually_updates_users_details(
        self, user, database, plugin_manager, mocker
    ):
        location = str(uuid4())
        details = UserDetailsChange(location=location)
        hook_impl = mocker.Mock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        handler = DefaultDetailsUpdateHandler(
            db=database, plugin_manager=plugin_manager
        )

        handler.apply_changeset(user, details)
        same_user = User.query.get(user.id)

        assert same_user.location == location
        hook_impl.post_process_changeset.assert_called_once_with(
            user=user, details_update=details
        )

    @staticmethod
    def impl(post_processor):
        class Impl:
            @HookimplMarker("flaskbb")
            def flaskbb_details_updated(self, user, details_update):
                post_processor.post_process_changeset(
                    user=user, details_update=details_update
                )

        return Impl()
