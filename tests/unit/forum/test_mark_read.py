from flask import g, get_flashed_messages
from flask_login import login_user, logout_user
from flaskbb.forum import views


def test_mark_forum_read_returns_to_the_page_it_was_sent_from(default_settings, user, forum):
    page = f"/forum/{forum.id}-{forum.slug}?page=2"
    headers = {"HX-Request": "true", "HX-Current-URL": f"http://localhost{page}"}

    with views.current_app.test_request_context(method="POST", headers=headers):
        # CanAccessForum resolves the forum off of g when it is not in the URL
        g.forum = forum
        try:
            login_user(user)
            response = views.MarkRead.as_view("markread")(forum_id=forum.id)
            messages = get_flashed_messages(with_categories=True)
            logout_user()
        finally:
            # g lives on the package-scoped app context and would leak
            g.pop("forum", None)

    assert response.status_code == 302
    assert response.headers["Location"] == page
    assert ("success", f"Forum {forum.title} marked as read.") in messages
