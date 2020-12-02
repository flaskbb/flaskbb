# -*- coding: utf-8 -*-
"""
    flaskbb.user.services.update
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    User update services.

    :copyright: (c) 2018 the FlaskBB Team.
    :license: BSD, see LICENSE for more details
"""

import attr

from ...core.exceptions import accumulate_errors
from ...core.changesets import ChangeSetHandler
from ...utils.database import try_commit


@attr.s(eq=False, order=False, frozen=True, repr=True, hash=False)
class DefaultDetailsUpdateHandler(ChangeSetHandler):
    """
    Validates and updates a user's details and persists the changes to the database.
    """

    db = attr.ib()
    plugin_manager = attr.ib()
    validators = attr.ib(factory=list)

    def apply_changeset(self, model, changeset):
        accumulate_errors(
            lambda v: v.validate(model, changeset), self.validators
        )
        changeset.assign_to_user(model)
        try_commit(self.db.session, "Could not update details")
        self.plugin_manager.hook.flaskbb_details_updated(
            user=model, details_update=changeset
        )


@attr.s(eq=False, order=False, frozen=True, repr=True, hash=False)
class DefaultPasswordUpdateHandler(ChangeSetHandler):
    """
    Validates and updates a user's password and persists the changes to the database.
    """

    db = attr.ib()
    plugin_manager = attr.ib()
    validators = attr.ib(factory=list)

    def apply_changeset(self, model, changeset):
        accumulate_errors(
            lambda v: v.validate(model, changeset), self.validators
        )
        model.password = changeset.new_password
        try_commit(self.db.session, "Could not update password")
        self.plugin_manager.hook.flaskbb_password_updated(user=model)


@attr.s(eq=False, order=False, frozen=True, repr=True, hash=False)
class DefaultEmailUpdateHandler(ChangeSetHandler):
    """
    Validates and updates a user's email and persists the changes to the database.
    """

    db = attr.ib()
    plugin_manager = attr.ib()
    validators = attr.ib(factory=list)

    def apply_changeset(self, model, changeset):
        accumulate_errors(lambda v: v.validate(model, changeset), self.validators)
        model.email = changeset.new_email
        try_commit(self.db.session, "Could not update email")
        self.plugin_manager.hook.flaskbb_email_updated(
            user=model, email_update=changeset
        )


@attr.s(eq=False, order=False, frozen=True, repr=True, hash=False)
class DefaultSettingsUpdateHandler(ChangeSetHandler):
    """
    Updates a user's settings and persists the changes to the database.
    """

    db = attr.ib()
    plugin_manager = attr.ib()

    def apply_changeset(self, model, changeset):
        changeset.assign_to_user(model)
        try_commit(self.db.session, "Could not update settings")
        self.plugin_manager.hook.flaskbb_settings_updated(
            user=model, settings_update=changeset
        )
