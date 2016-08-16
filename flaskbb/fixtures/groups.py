# -*- coding: utf-8 -*-
"""
    flaskbb.fixtures.groups
    ~~~~~~~~~~~~~~~~~~~~~~~

    The fixtures module for our groups.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""

from collections import OrderedDict


fixture = OrderedDict((
    ('Administrator', {
        'description': 'The Administrator Group',
        'admin': True,
        'super_mod': False,
        'mod': False,
        'banned': False,
        'guest': False,
        'editpost': True,
        'deletepost': True,
        'deletetopic': True,
        'posttopic': True,
        'postreply': True,
        'mod_edituser': True,
        'mod_banuser': True,
        'default_group': False,
    }),
    ('Super Moderator', {
        'description': 'The Super Moderator Group',
        'admin': False,
        'super_mod': True,
        'mod': False,
        'banned': False,
        'guest': False,
        'editpost': True,
        'deletepost': True,
        'deletetopic': True,
        'posttopic': True,
        'postreply': True,
        'mod_edituser': True,
        'mod_banuser': True,
        'default_group': False,
    }),
    ('Moderator', {
        'description': 'The Moderator Group',
        'admin': False,
        'super_mod': False,
        'mod': True,
        'banned': False,
        'guest': False,
        'editpost': True,
        'deletepost': True,
        'deletetopic': True,
        'posttopic': True,
        'postreply': True,
        'mod_edituser': True,
        'mod_banuser': True,
        'default_group': False,        
    }),
    ('Member', {
        'description': 'The Member Group',
        'admin': False,
        'super_mod': False,
        'mod': False,
        'banned': False,
        'guest': False,
        'editpost': True,
        'deletepost': False,
        'deletetopic': False,
        'posttopic': True,
        'postreply': True,
        'mod_edituser': False,
        'mod_banuser': False,
        'default_group': True,        
    }),
    ('Banned', {
        'description': 'The Banned Group',
        'admin': False,
        'super_mod': False,
        'mod': False,
        'banned': True,
        'guest': False,
        'editpost': False,
        'deletepost': False,
        'deletetopic': False,
        'posttopic': False,
        'postreply': False,
        'mod_edituser': False,
        'mod_banuser': False,
        'default_group': False,        
    }),
    ('Guest', {
        'description': 'The Guest Group',
        'admin': False,
        'super_mod': False,
        'mod': False,
        'banned': False,
        'guest': True,
        'editpost': False,
        'deletepost': False,
        'deletetopic': False,
        'posttopic': False,
        'postreply': False,
        'mod_edituser': False,
        'mod_banuser': False,
        'default_group': False,        
    })
))
