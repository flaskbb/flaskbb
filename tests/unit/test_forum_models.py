from datetime import datetime

from flask import current_app
from flask_login import login_user, current_user, logout_user

from flaskbb.forum.models import Category, Forum, Topic, Post, ForumsRead, \
    TopicsRead, Report
from flaskbb.user.models import User
from flaskbb.utils.settings import flaskbb_config


def test_category_save(database):
    """Test the save category method."""
    category = Category(title="Test Category")
    category.save()

    assert category.title == "Test Category"


def test_category_delete(category):
    """Test the delete category method."""
    category.delete()

    category = Category.query.filter_by(id=category.id).first()

    assert category is None


def test_category_delete_with_user(topic):
    """Test the delete category method with recounting the users post
    counts.
    """
    user = topic.user
    forum = topic.forum
    category = topic.forum.category

    assert user.post_count == 1
    assert forum.post_count == 1
    assert forum.topic_count == 1

    category.delete([user])

    assert user.post_count == 0

    category = Category.query.filter_by(id=category.id).first()
    topic = Topic.query.filter_by(id=topic.id).first()

    assert category is None
    # The topic should also be deleted
    assert topic is None


def test_category_delete_with_forum(forum):
    """When deleting a category, all of his forums should also be deleted."""
    forum.category.delete()

    assert forum is not None
    assert forum.category is not None

    category = Category.query.filter_by(id=forum.category.id).first()
    forum = Forum.query.filter_by(id=forum.id).first()

    assert forum is None
    assert category is None


def test_category_get_forums(forum, user):
    category = forum.category

    with current_app.test_request_context():
        # Test with logged in user
        login_user(user)
        assert current_user.is_authenticated
        cat, forums = Category.get_forums(category.id, current_user)

        # Check if it is a list because in a category there are normally more
        # than one forum in it (not in these tests)
        assert isinstance(forums, list) is True

        assert forums == [(forum, None)]
        assert cat == category

        # Test the same thing with a logged out user
        logout_user()
        assert not current_user.is_authenticated
        cat, forums = Category.get_forums(category.id, current_user)

        # Check if it is a list because in a category there are normally more
        # than one forum in it (not in these tests)
        assert isinstance(forums, list) is True

        assert forums == [(forum, None)]
        assert cat == category


def test_category_get_all(forum, user):
    category = forum.category

    with current_app.test_request_context():
        # Test with logged in user
        login_user(user)
        assert current_user.is_authenticated
        categories = Category.get_all(current_user)

        # All categories are stored in a list
        assert isinstance(categories, list)
        # The forums for a category are also stored in a list
        assert isinstance(categories[0][1], list)

        assert categories == [(category, [(forum, None)])]

        # Test with logged out user
        logout_user()
        assert not current_user.is_authenticated
        categories = Category.get_all(current_user)

        # All categories are stored in a list
        assert isinstance(categories, list)
        # The forums for a category are also stored in a list
        assert isinstance(categories[0][1], list)

        assert categories == [(category, [(forum, None)])]


def test_forum_save(category, moderator_user):
    """Test the save forum method"""
    forum = Forum(title="Test Forum", category_id=category.id)
    forum.moderators = [moderator_user]
    forum.save()

    assert forum.title == "Test Forum"
    assert forum.moderators == [moderator_user]


def test_forum_delete(forum):
    """Test the delete forum method."""
    forum.delete()

    forum = Forum.query.filter_by(id=forum.id).first()

    assert forum is None


def test_forum_delete_with_user_and_topic(topic, user):
    """Now test the delete forum method with a topic inside."""
    assert user.post_count == 1

    topic.forum.delete([user])

    forum = Forum.query.filter_by(id=topic.forum_id).first()

    assert forum is None

    assert user.post_count == 0


def test_forum_update_last_post(topic, user):
    """Test the update last post method."""
    post = Post(content="Test Content 2")
    post.save(topic=topic, user=user)

    assert topic.forum.last_post == post

    post.delete()

    topic.forum.update_last_post()

    assert topic.forum.last_post == topic.first_post


def test_forum_update_read(database, user, topic):
    """Test the update read method."""
    forumsread = ForumsRead.query.\
        filter(ForumsRead.user_id == user.id,
               ForumsRead.forum_id == topic.forum_id).first()

    topicsread = TopicsRead.query.\
        filter(TopicsRead.user_id == user.id,
               TopicsRead.topic_id == topic.id).first()

    forum = topic.forum

    with current_app.test_request_context():
        # Test with logged in user
        login_user(user)

        # Should return False because topicsread is None
        assert not forum.update_read(current_user, forumsread, topicsread)

        # This is the first time the user visits the topic
        topicsread = TopicsRead()
        topicsread.user_id = user.id
        topicsread.topic_id = topic.id
        topicsread.forum_id = topic.forum_id
        topicsread.last_read = datetime.utcnow()
        topicsread.save()

        # hence, we also need to create a new forumsread entry
        assert forum.update_read(current_user, forumsread, topicsread)

        forumsread = ForumsRead.query.\
            filter(ForumsRead.user_id == user.id,
                   ForumsRead.forum_id == topic.forum_id).first()

        # everything should be up-to-date now
        assert not forum.update_read(current_user, forumsread, topicsread)

        post = Post(content="Test Content")
        post.save(user=user, topic=topic)

        # Updating the topicsread tracker
        topicsread.last_read = datetime.utcnow()
        topicsread.save()

        # now the forumsread tracker should also need a update
        assert forum.update_read(current_user, forumsread, topicsread)

        logout_user()
        # should fail because the user is logged out
        assert not forum.update_read(current_user, forumsread, topicsread)


def test_forum_update_read_two_topics(database, user, topic, topic_moderator):
    """Test if the ForumsRead tracker will be updated if there are two topics
    and where one is unread and the other is read.
    """
    forumsread = ForumsRead.query.\
        filter(ForumsRead.user_id == user.id,
               ForumsRead.forum_id == topic.forum_id).first()

    forum = topic.forum

    with current_app.test_request_context():
        # Test with logged in user
        login_user(user)

        # This is the first time the user visits the topic
        topicsread = TopicsRead()
        topicsread.user_id = user.id
        topicsread.topic_id = topic.id
        topicsread.forum_id = topic.forum_id
        topicsread.last_read = datetime.utcnow()
        topicsread.save()

        # will not create a entry because there is still one unread topic
        assert not forum.update_read(current_user, forumsread, topicsread)


def test_forum_url(forum):
    assert forum.url == "http://localhost:5000/forum/1-test-forum"


def test_forum_slugify(forum):
    assert forum.slug == "test-forum"


def test_forum_get_forum(forum, user):
    with current_app.test_request_context():
        # Test with logged in user
        login_user(user)

        forum_with_forumsread = \
            Forum.get_forum(forum_id=forum.id, user=current_user)

        assert forum_with_forumsread == (forum, None)

        # Test with logged out user
        logout_user()

        forum_with_forumsread = \
            Forum.get_forum(forum_id=forum.id, user=current_user)

        assert forum_with_forumsread == (forum, None)


def test_forum_get_topics(topic, user):
    forum = topic.forum
    with current_app.test_request_context():
        # Test with logged in user
        login_user(user)

        topics = Forum.get_topics(forum_id=forum.id, user=current_user)

        assert topics.items == [(topic, topic.last_post, None)]

        # Test with logged out user
        logout_user()

        topics = Forum.get_topics(forum_id=forum.id, user=current_user)

        assert topics.items == [(topic, topic.last_post, None)]


def test_topic_save(forum, user):
    """Test the save topic method with creating and editing a topic."""
    post = Post(content="Test Content")
    topic = Topic(title="Test Title")

    assert forum.last_post_id is None
    assert forum.post_count == 0
    assert forum.topic_count == 0

    topic.save(forum=forum, post=post, user=user)

    assert topic.title == "Test Title"

    topic.title = "Test Edit Title"
    topic.save()

    assert topic.title == "Test Edit Title"

    # The first post in the topic is also the last post
    assert topic.first_post_id == post.id
    assert topic.last_post_id == post.id

    assert forum.last_post_id == post.id
    assert forum.post_count == 1
    assert forum.topic_count == 1


def test_topic_delete(topic):
    """Test the delete topic method"""
    assert topic.user.post_count == 1
    assert topic.post_count == 1
    assert topic.forum.topic_count == 1
    assert topic.forum.post_count == 1

    topic.delete()

    forum = Forum.query.filter_by(id=topic.forum_id).first()
    user = User.query.filter_by(id=topic.user_id).first()
    topic = Topic.query.filter_by(id=topic.id).first()

    assert topic is None
    assert user.post_count == 0
    assert forum.topic_count == 0
    assert forum.post_count == 0
    assert forum.last_post_id is None


def test_topic_move(topic):
    """Tests the topic move method."""
    forum_other = Forum(title="Test Forum 2", category_id=1)
    forum_other.save()

    forum_old = Forum.query.filter_by(id=topic.forum_id).first()

    assert topic.move(forum_other)

    assert forum_old.topics.all() == []
    assert forum_old.last_post_id is None

    assert forum_old.topic_count == 0
    assert forum_old.post_count == 0

    assert forum_other.last_post_id == topic.last_post_id
    assert forum_other.topic_count == 1
    assert forum_other.post_count == 1


def test_topic_move_same_forum(topic):
    """You cannot move a topic within the same forum."""
    assert not topic.move(topic.forum)


def test_topic_tracker_needs_update(database, user, topic):
    """Tests if the topicsread tracker needs an update if a new post has been
    submitted.
    """
    forumsread = ForumsRead.query.\
        filter(ForumsRead.user_id == user.id,
               ForumsRead.forum_id == topic.forum_id).first()

    topicsread = TopicsRead.query.\
        filter(TopicsRead.user_id == user.id,
               TopicsRead.topic_id == topic.id).first()

    with current_app.test_request_context():
        assert topic.tracker_needs_update(forumsread, topicsread)

        # Update the tracker
        topicsread = TopicsRead()
        topicsread.user_id = user.id
        topicsread.topic_id = topic.id
        topicsread.forum_id = topic.forum_id
        topicsread.last_read = datetime.utcnow()
        topicsread.save()

        forumsread = ForumsRead()
        forumsread.user_id = user.id
        forumsread.forum_id = topic.forum_id
        forumsread.last_read = datetime.utcnow()
        forumsread.save()

        # Now the topic should be read
        assert not topic.tracker_needs_update(forumsread, topicsread)

        post = Post(content="Test Content")
        post.save(topic=topic, user=user)

        assert topic.tracker_needs_update(forumsread, topicsread)


def test_untracking_topic_does_not_delete_it(database, user, topic):
    user.track_topic(topic)
    user.save()
    user.untrack_topic(topic)

    # Note that instead of returning None from the query below, the
    # unpatched verson will actually raise a DetachedInstanceError here,
    # due to the fact that some relationships don't get configured in
    # tests correctly and deleting would break them or something.  The
    # test still fails for the same reason, however: the topic gets
    # (albeit unsuccessfully) deleted when it is removed from
    # topictracker, when it clearly shouldn't be.
    user.save()

    assert Topic.query.filter(Topic.id == topic.id).first()


def test_topic_tracker_needs_update_cleared(database, user, topic):
    """Tests if the topicsread needs an update if the forum has been marked
    as cleared.
    """
    forumsread = ForumsRead.query.\
        filter(ForumsRead.user_id == user.id,
               ForumsRead.forum_id == topic.forum_id).first()

    topicsread = TopicsRead.query.\
        filter(TopicsRead.user_id == user.id,
               TopicsRead.topic_id == topic.id).first()

    with current_app.test_request_context():
        assert topic.tracker_needs_update(forumsread, topicsread)

        # Update the tracker
        forumsread = ForumsRead()
        forumsread.user_id = user.id
        forumsread.forum_id = topic.forum_id
        forumsread.last_read = datetime.utcnow()
        forumsread.cleared = datetime.utcnow()
        forumsread.save()

        # Now the topic should be read
        assert not topic.tracker_needs_update(forumsread, topicsread)


def test_topic_update_read(database, user, topic):
    """Tests the update read method if the topic is unread/read."""
    forumsread = ForumsRead.query.\
        filter(ForumsRead.user_id == user.id,
               ForumsRead.forum_id == topic.forum_id).first()

    with current_app.test_request_context():
        # Test with logged in user
        login_user(user)
        assert current_user.is_authenticated

        # Update the tracker
        assert topic.update_read(current_user, topic.forum, forumsread)
        # Because the tracker is already up-to-date, it shouldn't update it
        # again.
        assert not topic.update_read(current_user, topic.forum, forumsread)

        # Adding a new post - now the tracker shouldn't be up-to-date anymore.
        post = Post(content="Test Content")
        post.save(topic=topic, user=user)

        forumsread = ForumsRead.query.\
            filter(ForumsRead.user_id == user.id,
                   ForumsRead.forum_id == topic.forum_id).first()

        # Test tracker length
        flaskbb_config["TRACKER_LENGTH"] = 0
        assert not topic.update_read(current_user, topic.forum, forumsread)
        flaskbb_config["TRACKER_LENGTH"] = 1
        assert topic.update_read(current_user, topic.forum, forumsread)

        # Test with logged out user
        logout_user()
        assert not current_user.is_authenticated
        assert not topic.update_read(current_user, topic.forum, forumsread)


def test_topic_url(topic):
    assert topic.url == "http://localhost:5000/topic/1-test-topic-normal"


def test_topic_slug(topic):
    assert topic.slug == "test-topic-normal"


def test_post_save(topic, user):
    """Tests the save post method."""
    post = Post(content="Test Content")
    post.save(topic=topic, user=user)

    assert post.content == "Test Content"

    post.content = "Test Edit Content"
    post.save()

    assert post.content == "Test Edit Content"

    assert topic.user.post_count == 2
    assert topic.post_count == 2
    assert topic.last_post == post
    assert topic.forum.post_count == 2


def test_post_delete(topic):
    """Tests the delete post method with three different post types.
    The three types are:
        * First Post
        * A post between the first and last post (middle)
        * Last Post
    """
    post_middle = Post(content="Test Content Middle")
    post_middle.save(topic=topic, user=topic.user)
    assert topic.post_count == 2  # post_middle + first_post

    post_last = Post(content="Test Content Last")
    post_last.save(topic=topic, user=topic.user)

    # first post + post_middle + post_last
    assert topic.post_count == 3
    assert topic.forum.post_count == 3
    assert topic.user.post_count == 3

    post_middle.delete()

    # Check the last posts
    assert topic.last_post == post_last
    assert topic.forum.last_post == post_last
    assert topic.post_count == 2

    post_last.delete()

    # only the first_post remains
    assert topic.post_count == 1
    assert topic.forum.post_count == 1
    assert topic.user.post_count == 1
    assert topic.first_post_id == topic.last_post_id

    assert topic.forum.last_post_id == topic.last_post_id


def test_report(topic, user):
    """Tests if the reports can be saved/edited and deleted with the
    implemented save and delete methods."""
    report = Report(reason="Test Report")
    report.save(user=user, post=topic.first_post)
    assert report.reason == "Test Report"

    report.reason = "Test Report Edited"
    report.save()
    assert report.reason == "Test Report Edited"

    report.delete()
    report = Report.query.filter_by(id=report.id).first()
    assert report is None


def test_forumsread(topic, user):
    """Tests if the forumsread tracker can be saved/edited and deleted with the
    implemented save and delete methods."""
    forumsread = ForumsRead()
    forumsread.user_id = user.id
    forumsread.forum_id = topic.forum_id
    forumsread.last_read = datetime.utcnow()
    forumsread.save()
    assert forumsread is not None

    forumsread.delete()
    forumsread = ForumsRead.query.\
        filter_by(forum_id=forumsread.forum_id).\
        first()
    assert forumsread is None


def test_topicsread(topic, user):
    """Tests if the topicsread tracker can be saved/edited and deleted with the
    implemented save and delete methods."""
    topicsread = TopicsRead()
    topicsread.user_id = user.id
    topicsread.topic_id = topic.id
    topicsread.forum_id = topic.forum_id
    topicsread.last_read = datetime.utcnow()
    topicsread.save()
    assert topicsread is not None

    topicsread.delete()
    topicsread = TopicsRead.query.\
        filter_by(topic_id=topicsread.topic_id).\
        first()
    assert topicsread is None


def test_hiding_post_updates_counts(forum, topic, user):
    new_post = Post(content='spam')
    new_post.save(user=user, topic=topic)
    new_post.hide(user)
    assert user.post_count == 1
    assert topic.post_count == 1
    assert forum.post_count == 1
    assert topic.last_post != new_post
    assert forum.last_post != new_post
    assert new_post.hidden_by == user
    new_post.unhide()
    assert topic.post_count == 2
    assert user.post_count == 2
    assert forum.post_count == 2
    assert topic.last_post == new_post
    assert forum.last_post == new_post
    assert new_post.hidden_by is None


def test_hiding_topic_updates_counts(forum, topic, user):
    assert forum.post_count == 1
    topic.hide(user)
    assert forum.post_count == 0
    assert topic.hidden_by == user
    assert forum.last_post is None
    topic.unhide()
    assert forum.post_count == 1
    assert topic.hidden_by is None
    assert forum.last_post == topic.last_post


def test_hiding_first_post_hides_topic(forum, topic, user):
    assert forum.post_count == 1
    topic.first_post.hide(user)
    assert forum.post_count == 0
    assert topic.hidden_by == user
    assert forum.last_post is None
    topic.first_post.unhide()
    assert forum.post_count == 1
    assert topic.hidden_by is None
    assert forum.last_post == topic.last_post


def test_retrieving_hidden_posts(topic, user):
    new_post = Post(content='stuff')
    new_post.save(user, topic)
    new_post.hide(user)

    assert Post.query.get(new_post.id) is None
    assert Post.query.with_hidden().get(new_post.id) == new_post
    assert Post.query.filter(Post.id == new_post.id).first() is None
    hidden_post = Post.query\
        .with_hidden()\
        .filter(Post.id == new_post.id)\
        .first()
    assert hidden_post == new_post


def test_retrieving_hidden_topics(topic, user):
    topic.hide(user)

    assert Topic.query.get(topic.id) is None
    assert Topic.query.with_hidden().get(topic.id) == topic
    assert Topic.query.filter(Topic.id == topic.id).first() is None
    hidden_topic = Topic.query\
        .with_hidden()\
        .filter(Topic.id == topic.id)\
        .first()
    assert hidden_topic == topic
