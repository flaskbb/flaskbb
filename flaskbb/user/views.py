# -*- coding: utf-8 -*-
"""
    flaskbb.user.views
    ~~~~~~~~~~~~~~~~~~~~

    The user view handles the user profile
    and the user settings from a signed in user.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime
from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask.ext.login import login_required, current_user

from flaskbb.extensions import db
from flaskbb.user.models import User, PrivateMessage
from flaskbb.user.forms import (ChangePasswordForm, ChangeEmailForm,
                                ChangeUserDetailsForm, NewMessage)


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


@user.route("/<username>/topics")
def view_all_topics(username):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    topics = user.all_topics(page)
    return render_template("user/all_topics.html", user=user, topics=topics)


@user.route("/<username>/posts")
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


@user.route("/messages")
@user.route("/messages/inbox")
@login_required
def inbox():
    messages = PrivateMessage.query.filter(
        PrivateMessage.user_id == current_user.id,
        PrivateMessage.draft == False,
        PrivateMessage.trash == False,
        db.not_(PrivateMessage.from_user_id == current_user.id)).all()
    return render_template("message/inbox.html", messages=messages)


@user.route("/messages/<int:id>/view")
@login_required
def view_message(id):
    message = PrivateMessage.query.filter_by(id=id).first()
    if message.unread:
        message.unread = False
        db.session.commit()
    return render_template("message/view_message.html", message=message)


@user.route("/messages/sent")
@login_required
def sent():
    messages = PrivateMessage.query.filter(
        PrivateMessage.user_id == current_user.id,
        PrivateMessage.draft == False,
        PrivateMessage.trash == False,
        db.not_(PrivateMessage.to_user_id == current_user.id)).all()
    return render_template("message/sent.html", messages=messages)


@user.route("/messages/trash")
@login_required
def trash():
    messages = PrivateMessage.query.filter(
        PrivateMessage.user_id == current_user.id,
        PrivateMessage.trash == True).all()
    return render_template("message/trash.html", messages=messages)


@user.route("/messages/draft")
@login_required
def drafts():
    messages = PrivateMessage.query.filter(
        PrivateMessage.user_id == current_user.id,
        PrivateMessage.draft == True,
        PrivateMessage.trash == False).all()
    return render_template("message/drafts.html", messages=messages)


@user.route("/messages/new", methods=["POST", "GET"])
@login_required
def new_message():
    form = NewMessage()
    to_user = request.args.get("to_user")

    if request.method == "POST":
        if "save_message" in request.form:
            to_user = User.query.filter_by(username=form.to_user.data).first()

            form.save(from_user=current_user.id,
                      to_user=to_user.id,
                      user_id=current_user.id,
                      unread=False,
                      as_draft=True)

            flash("Message saved!", "success")
            return redirect(url_for("user.drafts"))

        if "send_message" in request.form and form.validate():
            to_user = User.query.filter_by(username=form.to_user.data).first()

            # Save the message in the current users inbox
            form.save(from_user=current_user.id,
                      to_user=to_user.id,
                      user_id=current_user.id,
                      unread=False)

            # Save the message in the recievers inbox
            form.save(from_user=current_user.id,
                      to_user=to_user.id,
                      user_id=to_user.id,
                      unread=True)

            flash("Message sent!", "success")
            return redirect(url_for("user.sent"))
    else:
        form.to_user.data = to_user

    return render_template("message/new_message.html", form=form)


@user.route("/messages/<int:id>/move")
@login_required
def move_message(id):
    message = PrivateMessage.query.filter_by(id=id).first_or_404()
    message.trash = True
    message.save()
    flash("Message moved to Trash!", "success")
    return redirect(url_for("user.inbox"))


@user.route("/messages/<int:id>/delete")
@login_required
def delete_message(id):
    message = PrivateMessage.query.filter_by(id=id).first_or_404()
    message.delete()
    flash("Message deleted!", "success")
    return redirect(url_for("user.inbox"))
