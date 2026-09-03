"""
flaskbb.utils.proxies
~~~~~~~~~~~~~~~~~~~~~

Typed re-exports of the context locals FlaskBB uses.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from typing import Any, cast, TYPE_CHECKING

from flask_login import current_user as _current_user

if TYPE_CHECKING:
    from flaskbb.user.models import User

# ``Guest`` stands in for anonymous visitors and only implements the subset of
# ``User`` that is reachable without an ``is_authenticated`` check
current_user: "User" = cast(Any, _current_user)
