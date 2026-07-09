# -*- coding: utf-8 -*-
"""
flaskbb.user.services.update
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

User update services.

:copyright: (c) 2018 the FlaskBB Team.
:license: BSD, see LICENSE for more details
"""

import os
from typing import override

from attrs import define, field
from flask_sqlalchemy import SQLAlchemy

from flaskbb.core.user.update import (
    AvatarUpdate,
    EmailUpdate,
    PasswordUpdate,
    SettingsUpdate,
    UserDetailsChange,
)
from flaskbb.plugins.manager import FlaskBBPluginManager
from flaskbb.user.models import User
from flaskbb.utils.uploads import get_avatar_filename, get_avatar_upload_path

from ...core.changesets import ChangeSetHandler, ChangeSetValidator
from ...core.exceptions import accumulate_errors
from ...utils.database import try_commit


@define(eq=False, order=False, frozen=True, repr=True, hash=False)
class DefaultDetailsUpdateHandler(ChangeSetHandler[User, UserDetailsChange]):
    """
    Validates and updates a user's details and persists the changes to the database.
    """

    db: SQLAlchemy = field()
    plugin_manager: FlaskBBPluginManager = field()
    validators: list[ChangeSetValidator[User, UserDetailsChange]] = field(factory=list)

    @override
    def apply_changeset(self, model: User, changeset: UserDetailsChange):
        accumulate_errors(lambda v: v.validate(model, changeset), self.validators)
        changeset.assign_to_user(model)
        try_commit(self.db.session, "Could not update details")
        self.plugin_manager.hook.flaskbb_details_updated(
            user=model, details_update=changeset
        )


@define(eq=False, order=False, frozen=True, repr=True, hash=False)
class DefaultAvatarUpdateHandler(ChangeSetHandler[User, AvatarUpdate]):
    """
    Validates and updates a user's password and persists the changes to the database.
    """

    db: SQLAlchemy = field()
    plugin_manager: FlaskBBPluginManager = field()
    validators: list[ChangeSetValidator[User, AvatarUpdate]] = field(factory=list)

    @override
    def apply_changeset(self, model: User, changeset: AvatarUpdate):
        accumulate_errors(lambda v: v.validate(model, changeset), self.validators)

        filename = get_avatar_filename(model.username, changeset.avatar.filename)
        changeset.avatar.save(os.path.join(get_avatar_upload_path(), filename))
        model.avatar = filename
        try_commit(self.db.session, "Could not update avatar")
        self.plugin_manager.hook.flaskbb_avatar_updated(user=model)


@define(eq=False, order=False, frozen=True, repr=True, hash=False)
class DefaultPasswordUpdateHandler(ChangeSetHandler[User, PasswordUpdate]):
    """
    Validates and updates a user's password and persists the changes to the database.
    """

    db: SQLAlchemy = field()
    plugin_manager: FlaskBBPluginManager = field()
    validators: list[ChangeSetValidator[User, PasswordUpdate]] = field(factory=list)

    @override
    def apply_changeset(self, model: User, changeset: PasswordUpdate):
        accumulate_errors(lambda v: v.validate(model, changeset), self.validators)
        model.password = changeset.new_password
        try_commit(self.db.session, "Could not update password")
        self.plugin_manager.hook.flaskbb_password_updated(user=model)


@define(eq=False, order=False, frozen=True, repr=True, hash=False)
class DefaultEmailUpdateHandler(ChangeSetHandler[User, EmailUpdate]):
    """
    Validates and updates a user's email and persists the changes to the database.
    """

    db: SQLAlchemy = field()
    plugin_manager: FlaskBBPluginManager = field()
    validators: list[ChangeSetValidator[User, EmailUpdate]] = field(factory=list)

    @override
    def apply_changeset(self, model: User, changeset: EmailUpdate):
        accumulate_errors(lambda v: v.validate(model, changeset), self.validators)
        model.email = changeset.new_email
        try_commit(self.db.session, "Could not update email")
        self.plugin_manager.hook.flaskbb_email_updated(
            user=model, email_update=changeset
        )


@define(eq=False, order=False, frozen=True, repr=True, hash=False)
class DefaultSettingsUpdateHandler(ChangeSetHandler[User, SettingsUpdate]):
    """
    Updates a user's settings and persists the changes to the database.
    """

    db: SQLAlchemy = field()
    plugin_manager: FlaskBBPluginManager = field()

    @override
    def apply_changeset(self, model: User, changeset: SettingsUpdate):
        changeset.assign_to_user(model)
        try_commit(self.db.session, "Could not update settings")
        self.plugin_manager.hook.flaskbb_settings_updated(
            user=model, settings_update=changeset
        )
