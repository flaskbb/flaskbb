from uuid import uuid4

import pytest
from pluggy import HookimplMarker

from flaskbb.core.changesets import ChangeSetPostProcessor, ChangeSetValidator
from flaskbb.core.exceptions import (PersistenceError, StopValidation,
                                     ValidationError)
from flaskbb.core.user.update import EmailUpdate
from flaskbb.user.models import User
from flaskbb.user.services.update import DefaultEmailUpdateHandler


def random_email():
    return "{}@not.real.at.all".format(str(uuid4()))


class TestDefaultEmailUpdateHandler(object):
    def test_raises_stop_validation_if_errors_occur(
        self, mocker, user, database, plugin_manager
    ):
        validator = mocker.Mock(spec=ChangeSetValidator)
        validator.validate.side_effect = ValidationError(
            "new_email", "That's not even valid"
        )
        hook_impl = mocker.Mock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        email_change = EmailUpdate(user.email, random_email())
        handler = DefaultEmailUpdateHandler(
            db=database, validators=[validator], plugin_manager=plugin_manager
        )

        with pytest.raises(StopValidation) as excinfo:
            handler.apply_changeset(user, email_change)

        assert excinfo.value.reasons == [("new_email", "That's not even valid")]
        hook_impl.post_process_changeset.assert_not_called()

    def test_raises_persistence_error_if_save_fails(
        self, mocker, user, plugin_manager
    ):
        email_change = EmailUpdate(user.email, random_email())
        db = mocker.Mock()
        db.session.commit.side_effect = Exception("no")
        hook_impl = mocker.Mock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        handler = DefaultEmailUpdateHandler(
            db=db, validators=[], plugin_manager=plugin_manager
        )

        with pytest.raises(PersistenceError) as excinfo:
            handler.apply_changeset(user, email_change)

        assert "Could not update email" in str(excinfo.value)
        hook_impl.post_process_changeset.assert_not_called()

    def test_actually_updates_email(
        self, user, database, mocker, plugin_manager
    ):
        new_email = random_email()
        email_change = EmailUpdate("test", new_email)
        hook_impl = mocker.Mock(spec=ChangeSetPostProcessor)
        plugin_manager.register(self.impl(hook_impl))
        handler = DefaultEmailUpdateHandler(
            db=database, validators=[], plugin_manager=plugin_manager
        )

        handler.apply_changeset(user, email_change)
        same_user = User.query.get(user.id)
        assert same_user.email == new_email
        hook_impl.post_process_changeset.assert_called_once_with(
            user=user, email_update=email_change
        )

    @staticmethod
    def impl(post_processor):
        class Impl:
            @HookimplMarker("flaskbb")
            def flaskbb_email_updated(self, user, email_update):
                post_processor.post_process_changeset(
                    user=user, email_update=email_update
                )

        return Impl()
