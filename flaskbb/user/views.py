# -*- coding: utf-8 -*-
"""
    flaskbb.user.views
    ~~~~~~~~~~~~~~~~~~~~

    The user view handles the user profile
    and the user settings from a signed in user.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from flask import Blueprint, render_template, flash, request
from flask.ext.login import login_required, current_user

from flaskbb.user.models import User
from flaskbb.user.forms import (ChangePasswordForm, ChangeEmailForm,
                                ChangeUserDetailsForm)

user = Blueprint("user", __name__)


@user.route("/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    days_registered = (datetime.utcnow() - user.date_joined).days
    if not days_registered:
        days_registered = 1

    posts_per_day = round((float(user.post_count) / float(days_registered)), 1)
    return render_template("user/profile.html", user=user,
                           days_registered=days_registered,
                           posts_per_day=posts_per_day)


@user.route("/<username>/all_topics")
def view_all_topics(username):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    topics = user.all_topics(page)
    return render_template("user/all_topics.html", user=user, topics=topics)


@user.route("/<username>/all_posts")
def view_all_posts(username):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.all_posts(page)
    return render_template("user/all_posts.html", user=user, posts=posts)


@user.route("/settings")
@login_required
def settings():
    return render_template("user/overview.html")


@user.route("/settings/change_password", methods=["POST", "GET"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password = form.new_password.data
        current_user.save()

        flash("Your password have been updated!", "success")
    return render_template("user/change_password.html", form=form)


@user.route("/settings/change_email", methods=["POST", "GET"])
@login_required
def change_email():
    form = ChangeEmailForm(current_user)
    if form.validate_on_submit():
        current_user.email = form.new_email.data
        current_user.save()

        flash("Your email have been updated!", "success")
    return render_template("user/change_email.html", form=form)


@user.route("/settings/change_user_details", methods=["POST", "GET"])
@login_required
def change_user_details():
    form = ChangeUserDetailsForm()
    if form.validate_on_submit():
        form.populate_obj(current_user)
        current_user.save()

        flash("Your details have been updated!", "success")
    else:
        form.birthday.data = current_user.birthday
        form.gender.data = current_user.gender
        form.location.data = current_user.location
        form.website.data = current_user.website
        form.avatar.data = current_user.avatar
        form.signature.data = current_user.signature
        form.notes.data = current_user.notes

    return render_template("user/change_user_details.html", form=form)
