"""
flaskbb.email
~~~~~~~~~~~~~

This module adds the functionality to send emails

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
from collections.abc import Callable
from typing import Any, cast

from celery import Task
from flask import render_template
from flask_babelplus import lazy_gettext as _
from flask_mail import Message
from kombu.exceptions import OperationalError

from flaskbb.extensions import celery, mail

logger = logging.getLogger(__name__)


def task(fn: Callable[..., None]) -> Task:
    """``celery.task`` is untyped, so a function decorated with it keeps its
    plain function type and ``.delay()`` is invisible to the type checker.

    Results are never read, and tracking them makes ``.delay()`` block for
    ~20s and raise ``RuntimeError`` when the result backend is unreachable.
    """
    return cast(Task, celery.task(fn, ignore_result=True))  # pyright: ignore[reportUnknownMemberType]


def delay_or_run(celery_task: Task, **kwargs: Any):
    """Queues ``celery_task``, or runs it in-process if the broker is
    unreachable. As in a worker, a failing task is logged, not raised.
    """
    try:
        celery_task.delay(**kwargs)  # pyright: ignore[reportUnknownMemberType]
    except OperationalError as e:
        logger.warning("Could not queue %s, running it in-process: %s", celery_task.name, e)
        try:
            celery_task(**kwargs)
        except Exception:
            logger.exception("Task %s failed", celery_task.name)


@task
def send_reset_token(token: str, username: str, email: str):
    """Sends the reset token to the user's email address.

    :param token: The token to send to the user
    :param username: The username to whom the email should be sent.
    :param email:  The email address of the user
    """
    send_email(
        subject=_("Password Recovery Confirmation"),
        recipients=[email],
        text_body=render_template("email/reset_password.txt", username=username, token=token),
        html_body=render_template("email/reset_password.html", username=username, token=token),
    )


@task
def send_activation_token(token: str, username: str, email: str):
    """Sends the activation token to the user's email address.

    :param token: The token to send to the user
    :param username: The username to whom the email should be sent.
    :param email:  The email address of the user
    """
    send_email(
        subject=_("Account Activation"),
        recipients=[email],
        text_body=render_template("email/activate_account.txt", username=username, token=token),
        html_body=render_template("email/activate_account.html", username=username, token=token),
    )


@task
def send_async_email(*args: Any, **kwargs: Any):
    send_email(*args, **kwargs)


def send_email(
    subject: str,
    recipients: list[str | tuple[str, str]],
    text_body: str,
    html_body: str,
    sender: str | tuple[str, str] | None = None,
):
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
