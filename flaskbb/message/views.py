# -*- coding: utf-8 -*-
"""
    flaskbb.message.views
    ~~~~~~~~~~~~~~~~~~~~~

    The views for the conversations and messages are located in this module.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from functools import wraps
import uuid

from flask import Blueprint, redirect, request, url_for, flash, abort
from flask.views import MethodView
from flask_login import login_required, current_user
from flask_babelplus import gettext as _

from flaskbb.extensions import db
from flaskbb.utils.settings import flaskbb_config
from flaskbb.utils.helpers import (format_quote, register_view,
                                   render_template, time_utcnow)
from flaskbb.message.forms import ConversationForm, MessageForm
from flaskbb.message.models import Conversation, Message
from flaskbb.user.models import User

message = Blueprint("message", __name__)


@message.route("/")
@message.route("/inbox")
@login_required
def inbox():
    page = request.args.get('page', 1, type=int)

    # the inbox will display both, the recieved and the sent messages
    conversations = Conversation.query. \
        filter(
            Conversation.user_id == current_user.id,
            Conversation.draft == False,
            Conversation.trash == False,
        ).\
        order_by(Conversation.date_modified.desc()). \
        paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)

    # we can't simply do conversations.total because it would ignore
    # drafted and trashed messages
    message_count = Conversation.query. \
        filter(Conversation.user_id == current_user.id).\
        count()

    return render_template("message/inbox.html", conversations=conversations,
                           message_count=message_count)


@message.route("/message/<int:message_id>/raw")
@login_required
def raw_message(message_id):
    message = Message.query.filter_by(id=message_id).first_or_404()

    # abort if the message was not the current_user's one or the one of the
    # recieved ones
    if not (message.conversation.from_user_id == current_user.id or
            message.conversation.to_user_id == current_user.id):
        abort(404)

    return format_quote(username=message.user.username,
                        content=message.message)


@message.route("/<int:conversation_id>/move", methods=["POST"])
@login_required
def move_conversation(conversation_id):
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        user_id=current_user.id
    ).first_or_404()

    conversation.trash = True
    conversation.save()

    return redirect(url_for("message.inbox"))


@message.route("/<int:conversation_id>/restore", methods=["POST"])
@login_required
def restore_conversation(conversation_id):
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        user_id=current_user.id
    ).first_or_404()

    conversation.trash = False
    conversation.save()
    return redirect(url_for("message.inbox"))


@message.route("/<int:conversation_id>/delete", methods=["POST"])
@login_required
def delete_conversation(conversation_id):
    conversation = Conversation.query.filter_by(
        id=conversation_id,
        user_id=current_user.id
    ).first_or_404()

    conversation.delete()
    return redirect(url_for("message.inbox"))


@message.route("/sent")
@login_required
def sent():
    page = request.args.get('page', 1, type=int)

    conversations = Conversation.query. \
        filter(
            Conversation.user_id == current_user.id,
            Conversation.draft == False,
            Conversation.trash == False,
            db.not_(Conversation.to_user_id == current_user.id)
        ).\
        order_by(Conversation.date_modified.desc()). \
        paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)

    message_count = Conversation.query. \
        filter(Conversation.user_id == current_user.id).\
        count()

    return render_template("message/sent.html", conversations=conversations,
                           message_count=message_count)


@message.route("/draft")
@login_required
def drafts():
    page = request.args.get('page', 1, type=int)

    conversations = Conversation.query. \
        filter(
            Conversation.user_id == current_user.id,
            Conversation.draft == True,
            Conversation.trash == False
        ).\
        order_by(Conversation.date_modified.desc()). \
        paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)

    message_count = Conversation.query. \
        filter(Conversation.user_id == current_user.id).\
        count()

    return render_template("message/drafts.html", conversations=conversations,
                           message_count=message_count)


@message.route("/trash")
@login_required
def trash():
    page = request.args.get('page', 1, type=int)

    conversations = Conversation.query. \
        filter(
            Conversation.user_id == current_user.id,
            Conversation.trash == True,
        ).\
        order_by(Conversation.date_modified.desc()). \
        paginate(page, flaskbb_config['TOPICS_PER_PAGE'], False)

    message_count = Conversation.query. \
        filter(Conversation.user_id == current_user.id).\
        count()

    return render_template("message/trash.html", conversations=conversations,
                           message_count=message_count)


def requires_message_box_space(f):

    @wraps(f)
    def wrapper(*a, **k):
        message_count = Conversation.query.filter(Conversation.user_id == current_user.id).count()

        if message_count >= flaskbb_config["MESSAGE_QUOTA"]:
            flash(
                _(
                    "You cannot send any messages anymore because you have "
                    "reached your message limit."
                ), "danger"
            )
            return redirect(url_for("message.inbox"))
        return f(*a, **k)

    return wrapper


class ViewConversation(MethodView):
    decorators = [login_required]
    form = MessageForm

    def get(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        if conversation.unread:
            conversation.unread = False
            current_user.invalidate_cache(permissions=False)
            conversation.save()

        form = self.form()
        return render_template("message/conversation.html", conversation=conversation, form=form)

    @requires_message_box_space
    def post(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        form = self.form()
        if form.validate_on_submit():
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
            conversation = Conversation.query.filter(
                Conversation.user_id == to_user_id,
                Conversation.shared_id == conversation.shared_id
            ).first()

            # user deleted the conversation, start a new conversation with just
            # the recieving message
            if conversation is None:
                conversation = Conversation(
                    subject=old_conv.subject,
                    from_user_id=current_user.id,
                    to_user=to_user_id,
                    user_id=to_user_id,
                    shared_id=old_conv.shared_id
                )
                conversation.save()

            form.save(conversation=conversation, user_id=current_user.id, unread=True)
            conversation.to_user.invalidate_cache(permissions=False)

            return redirect(url_for("message.view_conversation", conversation_id=old_conv.id))

        return render_template("message/conversation.html", conversation=conversation, form=form)


class NewConversation(MethodView):
    decorators = [requires_message_box_space, login_required]
    form = ConversationForm

    def get(self):
        form = self.form()
        form.to_user.data = request.args.get("to_user")
        return render_template("message/message_form.html", form=form, title=_("Compose Message"))

    def post(self):
        form = self.form()
        if "save_message" in request.form and form.validate():
            to_user = User.query.filter_by(username=form.to_user.data).first()

            shared_id = uuid.uuid4()

            form.save(
                from_user=current_user.id,
                to_user=to_user.id,
                user_id=current_user.id,
                unread=False,
                as_draft=True,
                shared_id=shared_id
            )

            flash(_("Message saved."), "success")
            return redirect(url_for("message.drafts"))

        if "send_message" in request.form and form.validate():
            to_user = User.query.filter_by(username=form.to_user.data).first()

            # this is the shared id between conversations because the messages
            # are saved on both ends
            shared_id = uuid.uuid4()

            # Save the message in the current users inbox
            form.save(
                from_user=current_user.id,
                to_user=to_user.id,
                user_id=current_user.id,
                unread=False,
                shared_id=shared_id
            )

            # Save the message in the recievers inbox
            form.save(
                from_user=current_user.id,
                to_user=to_user.id,
                user_id=to_user.id,
                unread=True,
                shared_id=shared_id
            )
            to_user.invalidate_cache(permissions=False)

            flash(_("Message sent."), "success")
            return redirect(url_for("message.sent"))

        return render_template("message/message_form.html", form=form, title=_("Compose Message"))


class EditConversation(MethodView):
    decorators = [login_required]
    form = ConversationForm

    def get(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        if not conversation.draft:
            flash(_("You cannot edit a sent message."), "danger")
            return redirect(url_for("message.inbox"))

        form = self.form()
        form.to_user.data = conversation.to_user.username
        form.subject.data = conversation.subject
        form.message.data = conversation.first_message.message

        return render_template("message/message_form.html", form=form, title=_("Edit Message"))

    def post(self, conversation_id):
        conversation = Conversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first_or_404()

        if not conversation.draft:
            flash(_("You cannot edit a sent message."), "danger")
            return redirect(url_for("message.inbox"))

        form = self.form()

        if request.method == "POST":
            if "save_message" in request.form:
                to_user = User.query.filter_by(username=form.to_user.data).first()

                conversation.draft = True
                conversation.to_user_id = to_user.id
                conversation.first_message.message = form.message.data
                conversation.save()

                flash(_("Message saved."), "success")
                return redirect(url_for("message.drafts"))

            if "send_message" in request.form and form.validate():
                to_user = User.query.filter_by(username=form.to_user.data).first()
                # Save the message in the recievers inbox
                form.save(
                    from_user=current_user.id,
                    to_user=to_user.id,
                    user_id=to_user.id,
                    unread=True,
                    shared_id=conversation.shared_id
                )

                # Move the message from ``Drafts`` to ``Sent``.
                conversation.draft = False
                conversation.to_user = to_user
                conversation.date_created = time_utcnow()
                conversation.save()

                flash(_("Message sent."), "success")
                return redirect(url_for("message.sent"))
        else:
            form.to_user.data = conversation.to_user.username
            form.subject.data = conversation.subject
            form.message.data = conversation.first_message.message

        return render_template("message/message_form.html", form=form, title=_("Edit Message"))


register_view(
    message,
    routes=["/<int:conversation_id>/view"],
    view_func=ViewConversation.as_view('view_conversation')
)
register_view(message, routes=["/new"], view_func=NewConversation.as_view('new_conversation'))
register_view(
    message,
    routes=["/<int:conversation_id>/edit"],
    view_func=EditConversation.as_view('edit_conversation')
)
