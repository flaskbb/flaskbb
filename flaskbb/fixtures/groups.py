"""
flaskbb.fixtures.groups
~~~~~~~~~~~~~~~~~~~~~~~

The fixtures module for our groups.

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from typing import Any

fixture: dict[str, dict[str, Any]] = {
    "Administrator": {
        "description": "The Administrator Group",
        "role": "admin",
        "permissions": {
            "editpost": True,
            "deletepost": True,
            "deletetopic": True,
            "posttopic": True,
            "postreply": True,
            "postattachment": True,
            "mod_edituser": True,
            "mod_banuser": True,
            "viewhidden": True,
            "makehidden": True,
        },
    },
    "Super Moderator": {
        "description": "The Super Moderator Group",
        "role": "super_mod",
        "permissions": {
            "editpost": True,
            "deletepost": True,
            "deletetopic": True,
            "posttopic": True,
            "postreply": True,
            "postattachment": True,
            "mod_edituser": True,
            "mod_banuser": True,
            "viewhidden": True,
            "makehidden": True,
        },
    },
    "Moderator": {
        "description": "The Moderator Group",
        "role": "mod",
        "permissions": {
            "editpost": True,
            "deletepost": True,
            "deletetopic": True,
            "posttopic": True,
            "postreply": True,
            "postattachment": True,
            "mod_edituser": True,
            "mod_banuser": True,
            "viewhidden": True,
            "makehidden": False,
        },
    },
    "Member": {
        "description": "The Member Group",
        "role": "member",
        "permissions": {
            "editpost": True,
            "deletepost": False,
            "deletetopic": False,
            "posttopic": True,
            "postreply": True,
            "postattachment": True,
            "mod_edituser": False,
            "mod_banuser": False,
            "viewhidden": False,
            "makehidden": False,
        },
    },
    "Banned": {
        "description": "The Banned Group",
        "role": "banned",
        "permissions": {
            "editpost": False,
            "deletepost": False,
            "deletetopic": False,
            "posttopic": False,
            "postreply": False,
            "postattachment": False,
            "mod_edituser": False,
            "mod_banuser": False,
            "viewhidden": False,
            "makehidden": False,
        },
    },
    "Guest": {
        "description": "The Guest Group",
        "role": "guest",
        "permissions": {
            "editpost": False,
            "deletepost": False,
            "deletetopic": False,
            "posttopic": False,
            "postreply": False,
            "postattachment": False,
            "mod_edituser": False,
            "mod_banuser": False,
            "viewhidden": False,
            "makehidden": False,
        },
    },
}
