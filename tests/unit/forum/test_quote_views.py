import pytest
from flask_login.test_client import FlaskLoginClient
from flaskbb.forum.models import Post, Topic

QUOTE_HEADER = '<header class="post-quote-header">'


@pytest.fixture
def client(application, user):
    application.test_client_class = FlaskLoginClient
    return application.test_client(user=user)


@pytest.fixture
def quoting_topic(forum, user, topic):
    post = topic.first_post
    quote = (
        f"> **[{post.username}](/user/{post.username}) wrote:** [view post](/post/{post.id})\n"
        f">\n> {post.content}\n\n"
    )

    quoting_topic = Topic(title="Quoting Topic")
    quoting_topic.save(forum=forum, user=user, post=Post(content=f"{quote}My reply."))
    return quoting_topic


def test_topic_page_renders_quote_headers(client, quoting_topic):
    post = quoting_topic.first_post

    response = client.get(f"/topic/{quoting_topic.id}")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert QUOTE_HEADER in html
    assert f'data-quote-post-url="/post/{post.id}"' in html
    assert 'class="btn btn-sm btn-primary selection-quote-btn"' in html


@pytest.mark.parametrize("page", ["posts", "topics"])
def test_profile_pages_render_quote_headers(client, quoting_topic, user, page):
    response = client.get(f"/user/{user.username}/{page}")

    assert response.status_code == 200
    assert QUOTE_HEADER in response.get_data(as_text=True)


def test_raw_post_links_the_quoted_post(client, topic):
    post = topic.first_post

    response = client.get(f"/post/{post.id}/raw")

    assert response.status_code == 200
    assert f"wrote:** [view post](/post/{post.id})" in response.get_data(as_text=True)


def test_full_reply_prefills_a_quote_linking_the_post(client, topic):
    post = topic.first_post

    response = client.get(f"/topic/{topic.id}/post/{post.id}/reply")

    assert response.status_code == 200
    assert f"wrote:** [view post](/post/{post.id})" in response.get_data(as_text=True)
