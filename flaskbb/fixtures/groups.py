# -*- coding: utf-8 -*-
"""
    flaskbb.fixtures.groups
    ~~~~~~~~~~~~~~~~~~~~~~~

    The fixtures module for our groups.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""

from collections import OrderedDict


roles = {
    "admin": "The administrator role",
    "super_mod": "The super moderator role",
    "mod": "The moderator role",
    "member": "The member role",
    "banned": "The banned role",
    "guest": "The guest role",

    "editpost": "The edit post permission",
    "deletepost": "The delete post permission",
    "deletetopic": "The delete topic permission",
    "postreply": "The post reply permission",
    "mod_edituser": "The edit user permission",
    "mod_banuser": "The ban user permission"
}

groups = OrderedDict((
    ("Administrator", {
        "description": "The Administrator Group",
        "roles": [
            "admin", "editpost", "deletepost", "deletetopic", "postreply",
            "posttopic", "mod_edituser", "mod_banuser"
        ]
    }),
    ("Super Moderator", {
        "description": "The Super Moderator Group",
        "roles": [
            "super_mod", "editpost", "deletepost", "deletetopic", "postreply",
            "posttopic", "mod_edituser", "mod_banuser"
        ]
    }),
    ("Moderator", {
        "description": "The Moderator Group",
        "roles": [
            "mod", "editpost", "deletepost", "deletetopic", "postreply",
            "posttopic", "mod_edituser", "mod_banuser"
        ]
    }),
    ("Member", {
        "description": "The Member Group",
        "roles": [
            "member", "editpost", "postreply", "posttopic"
        ]
    }),
    ("Banned", {
        "description": "The Banned Group",
        "roles": [
            "banned"
        ]
    }),
    ("Guest", {
        "description": "The Banned Group",
        "roles": [
            "guest"
        ]
    })
))
