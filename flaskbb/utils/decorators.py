# -*- coding: utf-8 -*-
"""
    flaskbb.utils.decorators
    ~~~~~~~~~~~~~~~~~~~~~~~~

    A place for our decorators.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from functools import wraps

from flask import abort
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_anonymous():
            abort(403)
        if not current_user.permissions['admin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def moderator_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.is_anonymous():
            abort(403)

        if not any([current_user.permissions['admin'],
                    current_user.permissions['super_mod'],
                    current_user.permissions['mod']]):
            abort(403)

        return f(*args, **kwargs)
    return decorated
