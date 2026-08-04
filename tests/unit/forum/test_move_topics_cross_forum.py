from flask_login.test_client import FlaskLoginClient
from flaskbb.forum.models import Category, Forum, Post, Topic
from flaskbb.user.models import User


def _setup_forums_and_topic(default_groups):
    category = Category(title="Test Category")
    category.save()

    forum_a = Forum(title="Forum A (attacker moderates this)", category_id=category.id)
    forum_a.groups = default_groups
    forum_a.save()

    forum_b = Forum(title="Forum B (attacker has zero rights here)", category_id=category.id)
    forum_b.groups = default_groups
    forum_b.save()

    victim = User(
        username="victim",
        email="victim@example.org",
        password="test",
        primary_group=default_groups[3],
        activated=True,
    )
    victim.save()

    victim_topic = Topic(title="Private topic in Forum B")
    victim_post = Post(content="content the attacker should not be able to touch")
    victim_topic.save(forum=forum_b, user=victim, post=victim_post)

    return forum_a, forum_b, victim_topic


def test_moderator_can_move_topic_from_unmoderated_forum(
    application, database, default_groups, default_settings
):
    forum_a, forum_b, victim_topic = _setup_forums_and_topic(default_groups)

    attacker = User(
        username="attacker_mod",
        email="attacker_mod@example.org",
        password="test",
        primary_group=default_groups[2],
        activated=True,
    )
    attacker.save()
    forum_a.moderators.append(attacker)  # attacker only moderates forum_a
    forum_a.save()

    assert victim_topic.forum_id == forum_b.id
    assert attacker not in forum_b.moderators

    application.config["WTF_CSRF_ENABLED"] = False
    application.test_client_class = FlaskLoginClient
    with application.test_client(user=attacker) as client:
        resp = client.post(
            f"/forum/{forum_a.id}/edit",
            data={
                "rowid": [str(victim_topic.id)],
                "move": "Move",
                "forum": str(forum_a.id),
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

    database.session.refresh(victim_topic)
    assert victim_topic.forum_id == forum_b.id


def test_non_moderator_cannot_move_topics_control(
    application, database, default_groups, default_settings
):
    forum_a, forum_b, victim_topic = _setup_forums_and_topic(default_groups)

    plain_member = User(
        username="plain_member",
        email="plain_member@example.org",
        password="test",
        primary_group=default_groups[3],
        activated=True,
    )
    plain_member.save()

    application.config["WTF_CSRF_ENABLED"] = False
    application.test_client_class = FlaskLoginClient
    with application.test_client(user=plain_member) as client:
        resp = client.post(
            f"/forum/{forum_a.id}/edit",
            data={
                "rowid": [str(victim_topic.id)],
                "move": "Move",
                "forum": str(forum_a.id),
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

    database.session.refresh(victim_topic)
    assert victim_topic.forum_id == forum_b.id
