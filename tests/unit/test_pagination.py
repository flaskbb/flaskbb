import sqlalchemy as sa
from flask import render_template_string
from flaskbb.extensions import db
from flaskbb.user.models import User


def test_pagination_links_load_into_the_page_content(request_context, default_settings, user):
    users = db.paginate(sa.select(User), page=1, per_page=1, error_out=False)

    rendered = render_template_string(
        "{% from '_macros/pagination.html' import render_pagination %}"
        "{{ render_pagination(users, '/memberlist') }}",
        users=users,
    )

    assert 'hx-boost="true"' in rendered
    assert 'hx-target="#page-content"' in rendered
    # the topic page's swap targets must not reach its pagination
    assert 'hx-select-oob="unset"' in rendered
