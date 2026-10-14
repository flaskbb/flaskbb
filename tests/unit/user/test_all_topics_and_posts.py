import pytest
from flaskbb.forum.models import Forum, Post, Topic
from flaskbb.user.models import Guest


def make_topic(forum, user, title):
    topic = Topic(title=title)
    return topic.save(forum=forum, user=user, post=Post(content=title))


def make_reply(topic, user, content):
    post = Post(content=content)
    return post.save(topic=topic, user=user)


@pytest.fixture
def user_content(request_context, category, forum, user, admin_user, default_groups):
    staff_forum = Forum(title="Staff Forum", category_id=category.id)
    staff_forum.save(groups=[default_groups[0]])

    visible = make_topic(forum, user, "Visible")
    make_topic(staff_forum, user, "Staff")
    hidden_topic = make_topic(forum, user, "Hidden topic")
    make_reply(hidden_topic, user, "Reply in hidden topic")
    hidden_topic.hide(admin_user)
    make_reply(visible, user, "Hidden reply").hide(admin_user)


@pytest.mark.parametrize("viewer", ["guest", "user"])
def test_lists_leave_out_restricted_forums_and_hidden_content(user_content, user, viewer):
    viewer = Guest() if viewer == "guest" else user

    topics = user.all_topics(1, viewer)
    posts = user.all_posts(1, viewer)

    assert [topic.title for topic in topics.items] == ["Visible"]
    assert [post.content for post in posts.items] == ["Visible"]
    assert topics.total == 1
    assert posts.total == 1


def test_lists_show_everything_to_admins(user_content, user, admin_user):
    topics = user.all_topics(1, admin_user)
    posts = user.all_posts(1, admin_user)

    assert [topic.title for topic in topics.items] == ["Hidden topic", "Staff", "Visible"]
    assert [post.content for post in posts.items] == [
        "Hidden reply",
        "Reply in hidden topic",
        "Hidden topic",
        "Staff",
        "Visible",
    ]
    assert topics.total == 3
    assert posts.total == 5
