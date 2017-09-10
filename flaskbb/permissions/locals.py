# -*- coding: utf-8 -*-
"""
    flaskbb.permissions.locals
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Thread local helpers for FlaskBB

    :copyright: 2017, the FlaskBB Team
    :license: BSD, see LICENSE for more details
"""

from flask import _request_ctx_stack, has_request_context
from flask_login import current_user
from flaskbb.forums.locals import current_category, current_forum
from werkzeug.local import LocalProxy

from .models import Permission
from .utils import PermissionManager


@LocalProxy
def current_permissions():
    """
    Loads the current permissions based on the user logged in and where in the application
    they are currently browsing
    """
    if has_request_context() and not hasattr(_request_ctx_stack.top, 'permissions'):
        all_perms = Permission.query.all()
        _request_ctx_stack.top.permissions = PermissionManager(
            all_permissions=all_perms,
            user=current_user,
            category=current_category,
            forum=current_forum
        )
    return getattr(_request_ctx_stack.top, 'permissions')
