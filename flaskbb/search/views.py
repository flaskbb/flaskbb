"""
flaskbb.search.views
~~~~~~~~~~~~~~~~~~~~~

The global search view.

:copyright: (c) 2014-2026 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging

from flask import Blueprint, Flask
from flask.views import MethodView
from pluggy import HookimplMarker

from flaskbb.extensions import db
from flaskbb.search.forms import SearchForm
from flaskbb.utils.helpers import register_view, render_template

impl = HookimplMarker("flaskbb")

logger = logging.getLogger(__name__)


class Search(MethodView):
    form = SearchForm

    def get(self):
        return render_template("search/search_form.html", form=self.form(), result=None)

    def post(self):
        form = self.form()
        result = None
        if form.validate_on_submit():
            result = {
                key: db.session.execute(stmt).unique().scalars().all()
                for key, stmt in form.get_results().items()
            }

        return render_template("search/search_form.html", form=form, result=result)


@impl(tryfirst=True)
def flaskbb_load_blueprints(app: Flask):
    search = Blueprint("search", __name__)
    register_view(search, routes=["/search"], view_func=Search.as_view("search"))

    app.register_blueprint(search, url_prefix=app.config["FORUM_URL_PREFIX"])
