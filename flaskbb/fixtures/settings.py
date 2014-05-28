# -*- coding: utf-8 -*-
"""
    flaskbb.fixtures.settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    The fixtures module for our settings.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""

fixture = (
    # Settings Group
    ('general', {
        'name': "General Settings",
        'description': "How many items per page are displayed.",
        'settings': (
            ('project_title', {
                'value':        "FlaskBB",
                'value_type':   "string",
                'input_type':   "text",
                'name':         "Project title",
                'description':  "The title of the project.",
            }),
            ('project_subtitle', {
                'value':        "A lightweight forum software in Flask",
                'value_type':   "string",
                'input_type':   "text",
                'name':         "Project subtitle",
                'description':  "A short description of the project.",
            }),
            ('posts_per_page', {
                'value':        10,
                'value_type':   "integer",
                'input_type':   "text",
                'extra':        {'min': 5},
                'name':         "Posts per page",
                'description':  "Number of posts displayed per page.",
            }),
            ('topics_per_page', {
                'value':        10,
                'value_type':   "integer",
                'input_type':   "text",
                'extra':        {'min': 5},
                'name':         "Topics per page",
                'description':  "Number of topics displayed per page.",
            }),
            ('users_per_page', {
                'value':        10,
                'value_type':   "integer",
                'input_type':   "text",
                'extra':        {'min': 5},
                'name':         "Users per page",
                'description':  "Number of users displayed per page.",
            }),
        ),
    }),
    ('misc', {
        'name': "Misc Settings",
        'description': "Miscellaneous settings.",
        'settings': (
            ('online_last_minutes', {
                'value':        15,
                'value_type':   "integer",
                'input_type':   "text",
                'extra':        {'min': 0},
                'name':         "Online last minutes",
                'description':  "How long a user can be inactive before he is marked as offline. 0 to disable it.",
            }),
            ('title_length', {
                'value':        15,
                'value_type':   "integer",
                'input_type':   "text",
                'extra':        {'min': 0},
                'name':         "Topic title length",
                'description':  "The length of the topic title shown on the index."
            }),
            ('tracker_length', {
                'value':        7,
                'value_type':   "integer",
                'input_type':   "text",
                'extra':        {'min': 0},
                'name':         "Tracker length",
                'description':  "The days for how long the forum should deal with unread topics. 0 to disable it."
            })
        ),
    }),
    ('themes', {
        'name': "Theme Settings",
        "description": "Change the appearance from your forum.",
        "settings": (
            # No settings for changing the theme because we are getting them
            #  from the extension
        )
    }),
)
