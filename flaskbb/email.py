# -*- coding: utf-8 -*-
"""
    flaskbb.emails
    ~~~~~~~~~~~~~~~~~~~~

    This module adds the functionality to send emails

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import render_template
from flask.ext.mail import Message
from flaskbb.extensions import mail
from flaskbb.decorators import async


def send_new_password(user, pw):
    send_email(
        subject="Password Reset",
        recipients=[user.email],
        text_body=render_template(
            "email/reset_password.txt",
            user=user,
            password=pw
        ),
        html_body=render_template(
            "email/reset_password.html",
            user=user,
            password=pw
        )
    )


@async
def send_async_email(msg):
    mail.send(msg)


def send_email(subject, recipients, text_body, html_body, sender=""):
    if not sender:
        msg = Message(subject, recipients=recipients)
    else:
        msg = Message(subject, recipients=recipients, sender=sender)

    msg.body = text_body
    msg.html = html_body
    send_async_email(msg)
