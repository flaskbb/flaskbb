# -*- coding: utf-8 -*-
"""
    flaskbb.decorators
    ~~~~~~~~~~~~~~~~~~~~

    A place for our decorators.

    :copyright: (c) 2013 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from threading import Thread
from functools import wraps

from flask import url_for, redirect
from flask.ext.login import current_user


def async(f):
    """
    A decorator for sending asynchronous mails
    """
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_anonymous():
            return redirect(url_for("frontend.index"))
        if not current_user.is_admin():
            return redirect(url_for("frontend.index"))
        return f(*args, **kwargs)
    return decorated
