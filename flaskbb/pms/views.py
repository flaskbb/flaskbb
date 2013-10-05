# -*- coding: utf-8 -*-
"""
    flaskbb.pms.views
    ~~~~~~~~~~~~~~~~~~~~

    This module contains the views that provides the functionality
    for creating and viewing private messages.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask.ext.login import login_required, current_user

from flaskbb.extensions import db
from flaskbb.user.models import User
from flaskbb.pms.forms import NewMessage
from flaskbb.pms.models import PrivateMessage

pms = Blueprint("pms", __name__)


@pms.route("/")
@pms.route("/inbox")
@login_required
def inbox():
    messages = PrivateMessage.query.filter(
        PrivateMessage.user_id == current_user.id,
        PrivateMessage.draft == False,
        PrivateMessage.trash == False,
        db.not_(PrivateMessage.from_user_id == current_user.id)).all()
    return render_template("pms/inbox.html", messages=messages)


@pms.route("/message/<int:id>")
@login_required
def view_message(id):
    message = PrivateMessage.query.filter_by(id=id).first()
    if message.unread:
        message.unread=False
        db.session.commit()
    return render_template("pms/view_message.html", message=message)


@pms.route("/sent")
@login_required
def sent():
    messages = PrivateMessage.query.filter(
        PrivateMessage.user_id == current_user.id,
        PrivateMessage.draft == False,
        PrivateMessage.trash == False,
        db.not_(PrivateMessage.to_user_id == current_user.id)).all()
    return render_template("pms/sent.html", messages=messages)


@pms.route("/trash")
@login_required
def trash():
    messages = PrivateMessage.query.filter(
        PrivateMessage.user_id == current_user.id,
        PrivateMessage.trash == True).all()
    return render_template("pms/trash.html", messages=messages)


@pms.route("/draft")
@login_required
def drafts():
    messages = PrivateMessage.query.filter(
        PrivateMessage.user_id == current_user.id,
        PrivateMessage.draft == True,
        PrivateMessage.trash == False).all()
    return render_template("pms/drafts.html", messages=messages)


@pms.route("/new", methods=["POST", "GET"])
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
                      unread=True,
                      as_draft=True)

            flash("Message saved!", "success")
            return redirect(url_for("pms.drafts"))

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
            return redirect(url_for("pms.sent"))
    else:
        form.to_user.data = to_user

    return render_template("pms/new_message.html", form=form)


@pms.route("/<int:id>/move")
@login_required
def move_message(id):
    message = PrivateMessage.query.filter_by(id=id).first()
    message.trash = True
    message.save()
    flash("Message moved to Trash!", "success")
    return redirect(url_for("pms.inbox"))


@pms.route("/<int:id>/delete")
@login_required
def delete_message(id):
    message = PrivateMessage.query.filter_by(id=id).first()
    message.delete()
    flash("Message deleted!", "success")
    return redirect(url_for("pms.inbox"))
