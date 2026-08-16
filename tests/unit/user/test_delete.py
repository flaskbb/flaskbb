from flaskbb.extensions import db
from flaskbb.forum.models import ForumsRead, TopicsRead, topictracker
from flaskbb.user.models import User


def test_delete_user_without_tracked_topics(database, user):
    user_id = user.id

    user.delete()

    assert db.session.get(User, user_id) is None


def test_delete_user_leaves_no_orphans(database, user, topic):
    user_id = user.id
    user.track_topic(topic)
    user.save()

    topicsread = TopicsRead()
    topicsread.user_id = user_id
    topicsread.topic_id = topic.id
    topicsread.forum_id = topic.forum_id
    topicsread.save()

    forumsread = ForumsRead()
    forumsread.user_id = user_id
    forumsread.forum_id = topic.forum_id
    forumsread.save()

    user.delete()

    assert db.session.get(User, user_id) is None
    assert (
        db.session.execute(db.select(topictracker).where(topictracker.c.user_id == user_id)).all()
        == []
    )
    assert (
        db.session.execute(db.select(TopicsRead).where(TopicsRead.user_id == user_id)).all() == []
    )
    assert (
        db.session.execute(db.select(ForumsRead).where(ForumsRead.user_id == user_id)).all() == []
    )
