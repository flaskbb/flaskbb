# -*- coding: utf-8 -*-
"""
    flaskbb.user.views
    ~~~~~~~~~~~~~~~~~~

    The user view handles the user profile
    and the user settings from a signed in user.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging

import attr
from flask import Blueprint, flash, redirect, request, url_for
from flask.views import MethodView
from flask_babelplus import gettext as _
from flask_login import current_user, login_required
from pluggy import HookimplMarker

from flaskbb.user.models import User
from flaskbb.utils.helpers import register_view, render_template

from ..core.exceptions import PersistenceError, StopValidation
from .services.factories import (
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


@attr.s(frozen=True, eq=False, order=False, hash=False, repr=True)
class UserSettings(MethodView):
    form = attr.ib(factory=settings_form_factory)
    settings_update_handler = attr.ib(factory=settings_update_handler)

    decorators = [login_required]

    def get(self):
        return self.render()

    def post(self):
        if self.form.validate_on_submit():
            try:
                self.settings_update_handler.apply_changeset(
                    current_user, self.form.as_change()
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


@attr.s(frozen=True, hash=False, eq=False, order=False, repr=True)
class ChangePassword(MethodView):
    form = attr.ib(factory=change_password_form_factory)
    password_update_handler = attr.ib(factory=password_update_handler)
    decorators = [login_required]

    def get(self):
        return self.render()

    def post(self):
        if self.form.validate_on_submit():
            try:
                self.password_update_handler.apply_changeset(
                    current_user, self.form.as_change()
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


@attr.s(frozen=True, eq=False, order=False, hash=False, repr=True)
class ChangeEmail(MethodView):
    form = attr.ib(factory=change_email_form_factory)
    update_email_handler = attr.ib(factory=email_update_handler)
    decorators = [login_required]

    def get(self):
        return self.render()

    def post(self):
        if self.form.validate_on_submit():
            try:
                self.update_email_handler.apply_changeset(
                    current_user, self.form.as_change()
                )
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


@attr.s(frozen=True, repr=True, eq=False, order=False, hash=False)
class ChangeUserDetails(MethodView):
    form = attr.ib(factory=change_details_form_factory)
    details_update_handler = attr.ib(factory=details_update_factory)
    decorators = [login_required]

    def get(self):
        return self.render()

    def post(self):

        if self.form.validate_on_submit():
            try:
                self.details_update_handler.apply_changeset(
                    current_user, self.form.as_change()
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
    def get(self, username):
        page = request.args.get("page", 1, type=int)
        user = User.query.filter_by(username=username).first_or_404()
        topics = user.all_topics(page, current_user)
        return render_template("user/all_topics.html", user=user, topics=topics)


class AllUserPosts(MethodView):  # pragma: no cover
    def get(self, username):
        page = request.args.get("page", 1, type=int)
        user = User.query.filter_by(username=username).first_or_404()
        posts = user.all_posts(page, current_user)
        return render_template("user/all_posts.html", user=user, posts=posts)


class UserProfile(MethodView):  # pragma: no cover
    def get(self, username):
        user = User.query.filter_by(username=username).first_or_404()
        return render_template("user/profile.html", user=user)


@impl(tryfirst=True)
def flaskbb_load_blueprints(app):
    user = Blueprint("user", __name__)
    register_view(
        user, routes=["/settings/email"], view_func=ChangeEmail.as_view("change_email")
    )
    register_view(
        user, routes=["/settings/general"], view_func=UserSettings.as_view("settings")
    )
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
        routes=["/<username>/posts"],
        view_func=AllUserPosts.as_view("view_all_posts"),
    )
    register_view(
        user,
        routes=["/<username>/topics"],
        view_func=AllUserTopics.as_view("view_all_topics"),
    )

    register_view(
        user, routes=["/<username>"], view_func=UserProfile.as_view("profile")
    )

    app.register_blueprint(user, url_prefix=app.config["USER_URL_PREFIX"])
