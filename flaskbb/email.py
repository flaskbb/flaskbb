# -*- coding: utf-8 -*-
"""
    flaskbb.emails
    ~~~~~~~~~~~~~~~~~~~~

    This module adds the functionality to send emails

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from threading import Thread
from flask import render_template, copy_current_request_context
from flask_mail import Message
from flask_babelplus import lazy_gettext as _

from flaskbb.extensions import mail


def send_reset_token(user, token):
    send_email(
        subject=_("Password Reset"),
        recipients=[user.email],
        text_body=render_template(
            "email/reset_password.txt",
            user=user,
            token=token
        ),
        html_body=render_template(
            "email/reset_password.html",
            user=user,
            token=token
        )
    )


def send_email(subject, recipients, text_body, html_body, sender=None):
    msg = Message(subject, recipients=recipients, sender=sender)
    msg.body = text_body
    msg.html = html_body

    @copy_current_request_context
    def send(msg):
        mail.send(msg)
    thr = Thread(target=send, args=[msg])
    thr.start()
