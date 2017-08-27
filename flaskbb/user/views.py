# -*- coding: utf-8 -*-
"""
    flaskbb.user.views
    ~~~~~~~~~~~~~~~~~~

    The user view handles the user profile
    and the user settings from a signed in user.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import Blueprint, flash, request
from flask.views import MethodView
from flask_login import login_required, current_user
from flask_babelplus import gettext as _

from flaskbb.utils.helpers import (get_available_languages,
                                   get_available_themes, register_view,
                                   render_template)
from flaskbb.user.models import User
from flaskbb.user.forms import (ChangePasswordForm, ChangeEmailForm,
                                ChangeUserDetailsForm, GeneralSettingsForm)


user = Blueprint("user", __name__)


@user.route("/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    return render_template("user/profile.html", user=user)


@user.route("/<username>/topics")
def view_all_topics(username):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    topics = user.all_topics(page, current_user)
    return render_template("user/all_topics.html", user=user, topics=topics)


@user.route("/<username>/posts")
def view_all_posts(username):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.all_posts(page, current_user)
    return render_template("user/all_posts.html", user=user, posts=posts)


class UserSettings(MethodView):
    decorators = [login_required]
    form = GeneralSettingsForm

    def get(self):
        form = self.form()

        form.theme.choices = get_available_themes()
        form.language.choices = get_available_languages()
        form.theme.data = current_user.theme
        form.language.data = current_user.language

        return render_template("user/general_settings.html", form=form)

    def post(self):
        form = self.form()

        form.theme.choices = get_available_themes()
        form.language.choices = get_available_languages()

        if form.validate_on_submit():
            current_user.theme = form.theme.data
            current_user.language = form.language.data
            current_user.save()

            flash(_("Settings updated."), "success")
        else:
            form.theme.data = current_user.theme
            form.language.data = current_user.language

        return render_template("user/general_settings.html", form=form)


class ChangePassword(MethodView):
    decorators = [login_required]
    form = ChangePasswordForm

    def get(self):
        return render_template("user/change_password.html", form=self.form())

    def post(self):
        form = self.form()
        if form.validate_on_submit():
            current_user.password = form.new_password.data
            current_user.save()

            flash(_("Password updated."), "success")
        return render_template("user/change_password.html", form=form)


class ChangeEmail(MethodView):
    decorators = [login_required]
    form = ChangeEmailForm

    def get(self):
        return render_template("user/change_email.html", form=self.form(current_user))

    def post(self):
        form = self.form(current_user)
        if form.validate_on_submit():
            current_user.email = form.new_email.data
            current_user.save()

            flash(_("Email address updated."), "success")
        return render_template("user/change_email.html", form=form)


class ChangeUserDetails(MethodView):
    decorators = [login_required]
    form = ChangeUserDetailsForm

    def get(self):
        return render_template("user/change_user_details.html", form=self.form(obh=current_user))

    def post(self):
        form = self.form(obj=current_user)

        if form.validate_on_submit():
            form.populate_obj(current_user)
            current_user.save()

            flash(_("User details updated."), "success")

        return render_template("user/change_user_details.html", form=form)


register_view(user, routes=['/settings/general'], view_func=UserSettings.as_view('settings'))
register_view(
    user, routes=['/settings/password'], view_func=ChangePassword.as_view('change_password')
)
register_view(user, routes=['/settings/email'], view_func=ChangeEmail.as_view('change_email'))
register_view(
    user,
    routes=["/settings/user-details"],
    view_func=ChangeUserDetails.as_view('change_user_details')
)
