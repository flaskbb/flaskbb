# -*- coding: utf-8 -*-
"""
    flaskbb.email
    ~~~~~~~~~~~~~

    This module adds the functionality to send emails

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from flask import render_template
from flask_mail import Message
from flask_babelplus import lazy_gettext as _

from flaskbb.extensions import mail
from flaskbb.utils.tokens import make_token


def send_reset_token(user):
    token = make_token(user=user, operation="reset_password")
    send_email(
        subject=_("Password Recovery Confirmation"),
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


def send_activation_token(user):
    token = make_token(user=user, operation="activate_account")
    send_email(
        subject=_("Account Activation"),
        recipients=[user.email],
        text_body=render_template(
            "email/activate_account.txt",
            user=user,
            token=token
        ),
        html_body=render_template(
            "email/activate_account.html",
            user=user,
            token=token
        )
    )


def send_email(subject, recipients, text_body, html_body, sender=None):
    msg = Message(subject, recipients=recipients, sender=sender)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)
