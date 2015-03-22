import uuid
from datetime import datetime

from flask import Blueprint, redirect, request, url_for, flash, abort
from flask_login import login_required, current_user
from flask_babelex import gettext as _

from flaskbb.extensions import db
from flaskbb.utils.settings import flaskbb_config
from flaskbb.utils.helpers import render_template, format_quote
from flaskbb.message.forms import ConversationForm, MessageForm
from flaskbb.message.models import Conversation, Message
from flaskbb.user.models import User

message = Blueprint("message", __name__)


@message.route("/")
@message.route("/inbox")
@login_required
def inbox():
    page = request.args.get('page', 1, type=int)

    conversations = Conversation.query.\
        filter(
            Conversation.user_id == current_user.id,
            Conversation.draft == False,
            Conversation.trash == False
        ).\
        order_by(Conversation.id.asc()).\
        paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)

    message_count = Conversation.query.\
        filter(Conversation.user_id == current_user.id).\
        count()

    return render_template("message/inbox.html", conversations=conversations,
                           message_count=message_count)


@message.route("/<int:conversation_id>/view", methods=["GET", "POST"])
def view_conversation(conversation_id):
    conversation = Conversation.query.filter_by(
        id=conversation_id).first_or_404()

    if conversation.user_id != current_user.id:
        # if a user tries to view a conversation which does not belong to him
        # just abort with 404
        abort(404)

    form = MessageForm()
    if form.validate_on_submit():

        message_count = Conversation.query.\
            filter(Conversation.user_id == current_user.id).\
            count()

        if message_count >= flaskbb_config["MESSAGE_QUOTA"]:
            flash(_("You cannot send any messages anymore because you have"
                    "reached your message limit."), "danger")
            return redirect(url_for("message.view_conversation",
                                    conversation_id=conversation.id))

        to_user_id = None
        # If the current_user is the user who recieved the message
        # then we have to change the id's a bit.
        if current_user.id == conversation.to_user_id:
            to_user_id = conversation.from_user_id
        else:
            to_user_id = conversation.to_user_id

        form.save(conversation=conversation, user_id=current_user.id)

        # save the message in the recievers conversation
        old_conv = conversation
        conversation = Conversation.query.\
            filter(
                Conversation.user_id == to_user_id,
                Conversation.shared_id == conversation.shared_id
            ).first()

        form.save(conversation=conversation, user_id=current_user.id,
                  unread=True)

        return redirect(url_for("message.view_conversation",
                                conversation_id=old_conv.id))

    return render_template("message/conversation.html",
                           conversation=conversation, form=form)


@message.route("/new", methods=["POST", "GET"])
@login_required
def new_conversation():
    form = ConversationForm()
    to_user = request.args.get("to_user")

    message_count = Conversation.query.\
        filter(Conversation.user_id == current_user.id).\
        count()

    if message_count >= flaskbb_config["MESSAGE_QUOTA"]:
        flash(_("You cannot send any messages anymore because you have"
                "reached your message limit."), "danger")
        return redirect(url_for("message.inbox"))

    if request.method == "POST":
        if "save_message" in request.form and form.validate():
            to_user = User.query.filter_by(username=form.to_user.data).first()

            form.save(from_user=current_user.id,
                      to_user=to_user.id,
                      user_id=current_user.id,
                      unread=False,
                      as_draft=True)

            flash(_("Message saved."), "success")
            return redirect(url_for("message.drafts"))

        if "send_message" in request.form and form.validate():
            to_user = User.query.filter_by(username=form.to_user.data).first()

            # this is the shared id between conversations because the messages
            # are saved on both ends
            shared_id = uuid.uuid4()

            # Save the message in the current users inbox
            form.save(from_user=current_user.id,
                      to_user=to_user.id,
                      user_id=current_user.id,
                      unread=False,
                      shared_id=shared_id)

            # Save the message in the recievers inbox
            form.save(from_user=current_user.id,
                      to_user=to_user.id,
                      user_id=to_user.id,
                      unread=True,
                      shared_id=shared_id)

            flash(_("Message sent."), "success")
            return redirect(url_for("message.sent"))
    else:
        form.to_user.data = to_user

    return render_template("message/message_form.html", form=form,
                           title=_("Compose Message"))


@message.route("/message/<int:message_id>/raw")
@login_required
def raw_message(message_id):
    message = Message.query.filter_by(id=message_id).first_or_404()

    if not (message.conversation.from_user_id == current_user.id or
            message.conversation.to_user_id == current_user.id):
        abort(404)

    return format_quote(username=message.user.username,
                        content=message.message)


@message.route("/<int:conversation_id>/edit", methods=["POST", "GET"])
@login_required
def edit_conversation(conversation_id):
    conversation = Conversation.query.filter_by(
        id=conversation_id).first_or_404()

    if conversation.user_id != current_user.id:
        # if a user tries to view a conversation which does not belong to him
        # just abort with 404
        abort(404)

    if not conversation.draft:
        flash(_("You cannot edit a sent message."), "danger")
        return redirect(url_for("message.inbox"))

    form = ConversationForm()

    if request.method == "POST":
        if "save_message" in request.form:
            to_user = User.query.filter_by(username=form.to_user.data).first()

            conversation.draft = True
            conversation.to_user = to_user.id
            conversation.save()

            flash(_("Message saved."), "success")
            return redirect(url_for("message.drafts"))

        if "send_message" in request.form and form.validate():
            to_user = User.query.filter_by(username=form.to_user.data).first()
            # Save the message in the recievers inbox
            form.save(from_user=current_user.id,
                      to_user=to_user.id,
                      user_id=to_user.id,
                      unread=True)

            # Move the message from ``Drafts`` to ``Sent``.
            conversation.draft = False
            conversation.to_user = to_user
            conversation.date_created = datetime.utcnow()
            conversation.save()

            flash(_("Message sent."), "success")
            return redirect(url_for("message.sent"))
    else:
        form.to_user.data = conversation.to_user.username
        form.subject.data = conversation.subject
        form.message.data = conversation.first_message

    return render_template("message/message_form.html", form=form,
                           title=_("Edit Message"))


@message.route("/sent")
@login_required
def sent():
    page = request.args.get('page', 1, type=int)

    conversations = Conversation.query.\
        filter(
            Conversation.user_id == current_user.id,
            Conversation.draft == False,
            Conversation.trash == False,
            db.not_(Conversation.to_user_id == current_user.id)
        ).\
        paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)

    message_count = Conversation.query.\
        filter(Conversation.user_id == current_user.id).\
        count()

    return render_template("message/sent.html", conversations=conversations,
                           message_count=message_count)


@message.route("/draft")
@login_required
def drafts():
    page = request.args.get('page', 1, type=int)

    conversations = Conversation.query.\
        filter(
            Conversation.user_id == current_user.id,
            Conversation.draft == True,
            Conversation.trash == False
        ).\
        paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)

    message_count = Conversation.query.\
        filter(Conversation.user_id == current_user.id).\
        count()

    return render_template("message/drafts.html", conversations=conversations,
                           message_count=message_count)


@message.route("/trash")
@login_required
def trash():
    page = request.args.get('page', 1, type=int)

    conversations = Conversation.query.\
        filter(
            Conversation.user_id == current_user.id,
            Conversation.trash == True,
        ).\
        paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)

    message_count = Conversation.query.\
        filter(Conversation.user_id == current_user.id).\
        count()

    return render_template("message/trash.html", conversations=conversations,
                           message_count=message_count)
