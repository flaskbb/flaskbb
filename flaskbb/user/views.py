"""
flaskbb.user.views
~~~~~~~~~~~~~~~~~~

The user view handles the user profile
and the user settings from a signed in user.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging

from attrs import define, field
from flask import Blueprint, flash, Flask, jsonify, redirect, request, url_for
from flask.views import MethodView
from flask_babelplus import gettext as _
from flask_login import current_user, login_required
from pluggy import HookimplMarker

from flaskbb.user.forms import (
    ChangeAvatarForm,
    ChangeEmailForm,
    ChangePasswordForm,
    ChangeUserDetailsForm,
    GeneralSettingsForm,
)
from flaskbb.user.models import User
from flaskbb.user.services.update import (
    DefaultAvatarUpdateHandler,
    DefaultDetailsUpdateHandler,
    DefaultEmailUpdateHandler,
    DefaultPasswordUpdateHandler,
    DefaultSettingsUpdateHandler,
)
from flaskbb.utils.helpers import real, register_view, render_template
from flaskbb.utils.uploads import delete_avatar_file

from ..core.exceptions import PersistenceError, StopValidation
from .services.factories import (
    avatar_update_handler,
    change_avatar_form_factory,
    change_details_form_factory,
    change_email_form_factory,
    change_password_form_factory,
    details_update_factory,
    email_update_handler,
    password_update_handler,
    settings_form_factory,
    settings_update_handler,
)

impl = HookimplMarker("flaskbb")

logger = logging.getLogger(__name__)


@define(frozen=True, eq=False, order=False, hash=False, repr=True)
class UserSettings(MethodView):
    form: GeneralSettingsForm = field(factory=settings_form_factory)
    settings_update_handler: DefaultSettingsUpdateHandler = field(factory=settings_update_handler)

    decorators = [login_required]

    def get(self):
        return self.render()

    def post(self):
        if self.form.validate_on_submit():
            try:
                self.settings_update_handler.apply_changeset(
                    real(current_user), self.form.as_change()
                )
            except StopValidation as e:
                self.form.populate_errors(e.reasons)
                return self.render()
            except PersistenceError:
                logger.exception("Error while updating user settings")
                flash(_("Error while updating user settings"), "danger")
                return self.redirect()

            flash(_("Settings updated."), "success")
            return self.redirect()
        return self.render()

    def render(self):
        return render_template("user/general_settings.html", form=self.form)

    def redirect(self):
        return redirect(url_for("user.settings"))


@define(frozen=True, hash=False, eq=False, order=False, repr=True)
class ChangePassword(MethodView):
    form: ChangePasswordForm = field(factory=change_password_form_factory)
    password_update_handler: DefaultPasswordUpdateHandler = field(factory=password_update_handler)
    decorators = [login_required]

    def get(self):
        return self.render()

    def post(self):
        if self.form.validate_on_submit():
            try:
                self.password_update_handler.apply_changeset(
                    real(current_user), self.form.as_change()
                )
            except StopValidation as e:
                self.form.populate_errors(e.reasons)
                return self.render()
            except PersistenceError:
                logger.exception("Error while changing password")
                flash(_("Error while changing password"), "danger")
                return self.redirect()

            flash(_("Password updated."), "success")
            return self.redirect()
        return self.render()

    def render(self):
        return render_template("user/change_password.html", form=self.form)

    def redirect(self):
        return redirect(url_for("user.change_password"))


@define(frozen=True, eq=False, order=False, hash=False, repr=True)
class ChangeEmail(MethodView):
    form: ChangeEmailForm = field(factory=change_email_form_factory)
    update_email_handler: DefaultEmailUpdateHandler = field(factory=email_update_handler)
    decorators = [login_required]

    def get(self):
        return self.render()

    def post(self):
        if self.form.validate_on_submit():
            try:
                self.update_email_handler.apply_changeset(real(current_user), self.form.as_change())
            except StopValidation as e:
                self.form.populate_errors(e.reasons)
                return self.render()
            except PersistenceError:
                logger.exception("Error while updating email")
                flash(_("Error while updating email"), "danger")
                return self.redirect()

            flash(_("Email address updated."), "success")
            return self.redirect()
        return self.render()

    def render(self):
        return render_template("user/change_email.html", form=self.form)

    def redirect(self):
        return redirect(url_for("user.change_email"))


@define(frozen=True, eq=False, order=False, hash=False, repr=True)
class ChangeAvatar(MethodView):
    form: ChangeAvatarForm = field(factory=change_avatar_form_factory)
    update_avatar_handler: DefaultAvatarUpdateHandler = field(factory=avatar_update_handler)
    decorators = [login_required]

    def get(self):
        return self.render()

    def post(self):
        if self.form.validate_on_submit():
            try:
                self.update_avatar_handler.apply_changeset(
                    real(current_user), self.form.as_change()
                )
            except StopValidation as e:
                self.form.populate_errors(e.reasons)
                return self.render()
            except PersistenceError:
                logger.exception("Error while updating avatar")
                flash(_("Error while updating avatar"), "danger")
                return self.redirect()

            flash(_("Avatar updated."), "success")
            return self.redirect()
        return self.render()

    def render(self):
        return render_template("user/change_avatar.html", form=self.form, user=current_user)

    def redirect(self):
        return redirect(url_for("user.change_avatar"))


class DeleteAvatar(MethodView):
    decorators = [login_required]

    def post(self, user_id: int | None = None):
        json = request.get_json(silent=True)

        user = None
        if json is None and user_id is not None:
            user = User.get_by(id=user_id)
        elif json is not None:
            user_id = json.get("user")
            if user_id:
                user_id = int(user_id)
                user = User.get_by(id=user_id)

        if user is None or current_user.id != user.id:
            return jsonify(
                message=_("You cannot delete an avatar from someone else."),
                category="danger",
                status=403,
            )

        delete_avatar_file(user.avatar)
        user.avatar = None
        user.save()
        return jsonify(
            message=_("Avatar deleted."),
            category="success",
            status=200,
        )


@define(frozen=True, repr=True, eq=False, order=False, hash=False)
class ChangeUserDetails(MethodView):
    form: ChangeUserDetailsForm = field(factory=change_details_form_factory)
    details_update_handler: DefaultDetailsUpdateHandler = field(factory=details_update_factory)
    decorators = [login_required]

    def get(self):
        return self.render()

    def post(self):
        if self.form.validate_on_submit():
            try:
                self.details_update_handler.apply_changeset(
                    real(current_user), self.form.as_change()
                )
            except StopValidation as e:
                self.form.populate_errors(e.reasons)
                return self.render()
            except PersistenceError:
                logger.exception("Error while updating user details")
                flash(_("Error while updating user details"), "danger")
                return self.redirect()

            flash(_("User details updated."), "success")
            return self.redirect()
        return self.render()

    def render(self):
        return render_template("user/change_user_details.html", form=self.form)

    def redirect(self):
        return redirect(url_for("user.change_user_details"))


class AllUserTopics(MethodView):  # pragma: no cover
    def get(self, username: str):
        page = request.args.get("page", 1, type=int)
        user = User.get_by_or_404(username=username)
        topics = user.all_topics(page, real(current_user))
        return render_template("user/all_topics.html", user=user, topics=topics)


class AllUserPosts(MethodView):  # pragma: no cover
    def get(self, username: str):
        page = request.args.get("page", 1, type=int)
        user = User.get_by_or_404(username=username)
        posts = user.all_posts(page, real(current_user))
        return render_template("user/all_posts.html", user=user, posts=posts)


class UserProfile(MethodView):  # pragma: no cover
    def get(self, username: str):
        user = User.get_by_or_404(username=username)
        return render_template("user/profile.html", user=user)


@impl(tryfirst=True)
def flaskbb_load_blueprints(app: Flask):
    user = Blueprint("user", __name__)
    register_view(user, routes=["/settings/email"], view_func=ChangeEmail.as_view("change_email"))
    register_view(user, routes=["/settings/general"], view_func=UserSettings.as_view("settings"))
    register_view(
        user,
        routes=["/settings/password"],
        view_func=ChangePassword.as_view("change_password"),
    )
    register_view(
        user,
        routes=["/settings/user-details"],
        view_func=ChangeUserDetails.as_view("change_user_details"),
    )
    register_view(
        user,
        routes=["/settings/avatar"],
        view_func=ChangeAvatar.as_view("change_avatar"),
    )
    register_view(
        user,
        routes=["/settings/avatar/delete"],
        view_func=DeleteAvatar.as_view("delete_avatar"),
    )
    register_view(
        user,
        routes=["/<username>/posts"],
        view_func=AllUserPosts.as_view("view_all_posts"),
    )
    register_view(
        user,
        routes=["/<username>/topics"],
        view_func=AllUserTopics.as_view("view_all_topics"),
    )

    register_view(user, routes=["/<username>"], view_func=UserProfile.as_view("profile"))

    app.register_blueprint(user, url_prefix=app.config["USER_URL_PREFIX"])
