# -*- coding: utf-8 -*-
"""
flaskbb.utils.views
~~~~~~~~~~~~~~~~~~~

This module contains some helpers for creating views.

:copyright: (c) 2016 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

from flask.views import View

from flaskbb.utils.helpers import render_template


class RenderableView(View):
    def __init__(self, template, view):
        self.template = template
        self.view = view

    def dispatch_request(self, *args, **kwargs):
        view_model = self.view(*args, **kwargs)
        return render_template(self.template, **view_model)
