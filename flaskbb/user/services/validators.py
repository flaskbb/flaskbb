# -*- coding: utf-8 -*-
"""
flaskbb.user.services.validators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Validators for use with user services.

:copyright: (c) 2018 the Flaskbb Team.
:license: BSD, see LICENSE for more details
"""

from typing import override

from attrs import define, field
from flask_babelplus import gettext as _
from requests.exceptions import RequestException
from sqlalchemy import func

from flaskbb.core.user.update import AvatarUpdate, EmailUpdate, PasswordUpdate
from flaskbb.user.models import User

from ...core.changesets import ChangeSetValidator
from ...core.exceptions import StopValidation, ValidationError
from ...utils.helpers import check_image


@define(eq=False, order=False, hash=False, frozen=True, repr=True)
class CantShareEmailValidator(ChangeSetValidator[User, EmailUpdate]):
    """
    Validates that the new email for the user isn't currently registered by
    another user.
    """

    users: type[User] = field()

    @override
    def validate(self, model: User, changeset: EmailUpdate):
        others = self.users.query.filter(
            self.users.id != model.id,
            func.lower(self.users.email) == changeset.new_email,
        ).count()

        if others != 0:
            raise ValidationError(
                "new_email",
                _("%(email)s is already registered", email=changeset.new_email),
            )


class OldEmailMustMatch(ChangeSetValidator[User, EmailUpdate]):
    """
    Validates that the email entered by the user is the current email of the user.
    """

    @override
    def validate(self, model: User, changeset: EmailUpdate):
        if model.email != changeset.old_email:
            raise StopValidation([("old_email", _("Old email does not match"))])


class EmailsMustBeDifferent(ChangeSetValidator[User, EmailUpdate]):
    """
    Validates that the new email entered by the user isn't the same as the
    current email for the user.
    """

    @override
    def validate(self, model: User, changeset: EmailUpdate):
        if model.email == changeset.new_email:
            raise ValidationError("new_email", _("New email address must be different"))


class PasswordsMustBeDifferent(ChangeSetValidator[User, PasswordUpdate]):
    """
    Validates that the new password entered by the user isn't the same as the
    current email for the user.
    """

    @override
    def validate(self, model: User, changeset: PasswordUpdate):
        if model.check_password(changeset.new_password):
            raise ValidationError("new_password", _("New password must be different"))


class OldPasswordMustMatch(ChangeSetValidator[User, PasswordUpdate]):
    """
    Validates that the old password entered by the user is the current password
    for the user.
    """

    @override
    def validate(self, model: User, changeset: PasswordUpdate):
        if not model.check_password(changeset.old_password):
            raise StopValidation([("old_password", _("Old password is wrong"))])


class ValidateAvatarURL(ChangeSetValidator[User, AvatarUpdate]):
    """
    Validates that the target avatar url currently meets constraints like
    height and width.

    .. warning::

        This validator only checks the **current** state of the image however
        if the image at the URL changes then this isn't re-run and the new
        image could break these contraints.
    """

    @override
    def validate(self, model: User, changeset: AvatarUpdate):
        if not changeset.avatar:
            return

        try:
            error, ignored = check_image(changeset.avatar)
            if error:
                raise ValidationError("avatar", error)
        except RequestException:
            raise ValidationError("avatar", _("Could not retrieve avatar"))
