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

from flask import Blueprint, flash, request, redirect, url_for
from flask.ext.login import login_required, current_user
from flask.ext.themes2 import get_themes_list
from flask.ext.babelex import gettext as _

from flaskbb.extensions import db, babel
from flaskbb.utils.helpers import render_template
from flaskbb.user.models import User, PrivateMessage
from flaskbb.user.forms import (ChangePasswordForm, ChangeEmailForm,
                                ChangeUserDetailsForm, GeneralSettingsForm,
                                NewMessageForm, EditMessageForm)


user = Blueprint("user", __name__)


@user.route("/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()

    return render_template("user/profile.html", user=user)


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


@user.route("/settings/general", methods=["POST", "GET"])
@login_required
def settings():
    form = GeneralSettingsForm()

    form.theme.choices = [(theme.identifier, theme.name)
                          for theme in get_themes_list()]

    form.language.choices = [(locale.language, locale.display_name)
                             for locale in babel.list_translations()]

    if form.validate_on_submit():
        current_user.theme = form.theme.data
        current_user.language = form.language.data
        current_user.save()

        flash(_("Your settings have been updated!"), "success")
    else:
        form.theme.data = current_user.theme
        form.theme.data = current_user.language

    return render_template("user/general_settings.html", form=form)


@user.route("/settings/password", methods=["POST", "GET"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password = form.new_password.data
        current_user.save()

        flash(_("Your password have been updated!"), "success")
    return render_template("user/change_password.html", form=form)


@user.route("/settings/email", methods=["POST", "GET"])
@login_required
def change_email():
    form = ChangeEmailForm(current_user)
    if form.validate_on_submit():
        current_user.email = form.new_email.data
        current_user.save()

        flash(_("Your email have been updated!"), "success")
    return render_template("user/change_email.html", form=form)


@user.route("/settings/user-details", methods=["POST", "GET"])
@login_required
def change_user_details():
    form = ChangeUserDetailsForm(obj=current_user)

    if form.validate_on_submit():
        form.populate_obj(current_user)
        current_user.save()

        flash(_("Your details have been updated!"), "success")

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


@user.route("/messages/<int:message_id>/view")
@login_required
def view_message(message_id):
    message = PrivateMessage.query.filter_by(id=message_id).first()
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
    form = NewMessageForm()
    to_user = request.args.get("to_user")

    if request.method == "POST":
        if "save_message" in request.form and form.validate():
            to_user = User.query.filter_by(username=form.to_user.data).first()

            form.save(from_user=current_user.id,
                      to_user=to_user.id,
                      user_id=current_user.id,
                      unread=False,
                      as_draft=True)

            flash(_("Message saved!"), "success")
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

            flash(_("Message sent!"), "success")
            return redirect(url_for("user.sent"))
    else:
        form.to_user.data = to_user

    return render_template("message/message_form.html", form=form,
                           title=_("Compose Message"))


@user.route("/messages/<int:message_id>/edit", methods=["POST", "GET"])
@login_required
def edit_message(message_id):
    message = PrivateMessage.query.filter_by(id=message_id).first_or_404()

    if not message.draft:
        flash(_("You cannot edit a sent message"), "danger")
        return redirect(url_for("user.inbox"))

    form = EditMessageForm()

    if request.method == "POST":
        if "save_message" in request.form:
            to_user = User.query.filter_by(username=form.to_user.data).first()

            # Move the message from ``Drafts`` to ``Sent``.
            message.draft = False
            message.to_user = to_user.id
            message.save()

            flash(_("Message saved!"), "success")
            return redirect(url_for("user.drafts"))

        if "send_message" in request.form and form.validate():
            to_user = User.query.filter_by(username=form.to_user.data).first()
            # Save the message in the recievers inbox
            form.save(from_user=current_user.id,
                      to_user=to_user.id,
                      user_id=to_user.id,
                      unread=True)

            # Move the message from ``Drafts`` to ``Sent``.
            message.draft = False
            message.to_user = to_user
            message.date_created = datetime.utcnow()
            message.save()

            flash(_("Message sent!"), "success")
            return redirect(url_for("user.sent"))
    else:
        form.to_user.data = message.to_user.username
        form.subject.data = message.subject
        form.message.data = message.message

    return render_template("message/message_form.html", form=form,
                           title=_("Edit Message"))


@user.route("/messages/<int:message_id>/move")
@login_required
def move_message(message_id):
    message = PrivateMessage.query.filter_by(id=message_id).first_or_404()
    message.trash = True
    message.save()
    flash(_("Message moved to Trash!"), "success")
    return redirect(url_for("user.inbox"))


@user.route("/messages/<int:message_id>/restore")
@login_required
def restore_message(message_id):
    message = PrivateMessage.query.filter_by(id=message_id).first_or_404()
    message.trash = False
    message.save()
    flash(_("Message restored from Trash!"), "success")
    return redirect(url_for("user.inbox"))


@user.route("/messages/<int:message_id>/delete")
@login_required
def delete_message(message_id):
    message = PrivateMessage.query.filter_by(id=message_id).first_or_404()
    message.delete()
    flash(_("Message deleted!"), "success")
    return redirect(url_for("user.inbox"))
