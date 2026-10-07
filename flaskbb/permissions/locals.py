"""
flaskbb.permissions.locals
~~~~~~~~~~~~~~~~~~~~~~~~~~

Thread local helpers for the permissions of the current request.

:copyright: (c) 2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from flask_login import current_user
from werkzeug.local import LocalProxy

from flaskbb.core.auth.permissions import UserPermissions
from flaskbb.utils.helpers import real

from .manager import permission_manager

current_permissions: LocalProxy[UserPermissions] = LocalProxy(
    lambda: permission_manager.for_user(real(current_user))
)
