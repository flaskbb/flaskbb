# -*- coding: utf-8 -*-
"""
    flaskbb.email
    ~~~~~~~~~~~~~

    This module adds the functionality to send emails

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging
from flask import render_template
from flask_mail import Message
from flask_babelplus import lazy_gettext as _

from flaskbb.extensions import mail, celery


logger = logging.getLogger(__name__)


@celery.task
def send_reset_token(token, username, email):
    """Sends the reset token to the user's email address.

    :param token: The token to send to the user
    :param username: The username to whom the email should be sent.
    :param email:  The email address of the user
    """
    send_email(
        subject=_("Password Recovery Confirmation"),
        recipients=[email],
        text_body=render_template(
            "email/reset_password.txt",
            username=username,
            token=token
        ),
        html_body=render_template(
            "email/reset_password.html",
            username=username,
            token=token
        )
    )


@celery.task
def send_activation_token(token, username, email):
    """Sends the activation token to the user's email address.

    :param token: The token to send to the user
    :param username: The username to whom the email should be sent.
    :param email:  The email address of the user
    """
    send_email(
        subject=_("Account Activation"),
        recipients=[email],
        text_body=render_template(
            "email/activate_account.txt",
            username=username,
            token=token
        ),
        html_body=render_template(
            "email/activate_account.html",
            username=username,
            token=token
        )
    )


@celery.task
def send_async_email(*args, **kwargs):
    send_email(*args, **kwargs)


def send_email(subject, recipients, text_body, html_body, sender=None):
    """Sends an email to the given recipients.

    :param subject: The subject of the email.
    :param recipients: A list of recipients.
    :param text_body: The text body of the email.
    :param html_body: The html body of the email.
    :param sender: A two-element tuple consisting of name and address.
                   If no sender is given, it will fall back to the one you
                   have configured with ``MAIL_DEFAULT_SENDER``.
    """
    msg = Message(subject, recipients=recipients, sender=sender)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)
