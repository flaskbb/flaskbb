from flaskbb.forum.models import Category, Forum, Topic, Post
from flaskbb.user.models import User


def test_category_save(database):
    category = Category(title="Test Category")
    category.save()

    assert category.title == "Test Category"


def test_category_delete(category):
    category.delete()

    category = Category.query.filter_by(id=category.id).first()

    assert category is None


def test_category_delete_with_user(topic_normal):
    user = topic_normal.user
    forum = topic_normal.forum
    category = topic_normal.forum.category

    assert user.post_count == 1
    assert forum.post_count == 1
    assert forum.topic_count == 1

    category.delete([user])

    assert user.post_count == 0

    category = Category.query.filter_by(id=category.id).first()
    topic = Topic.query.filter_by(id=topic_normal.id).first()

    assert category is None
    # The topic should also be deleted
    assert topic is None


def test_category_delete_with_forum(forum):
    forum.category.delete()

    assert forum is not None
    assert forum.category is not None

    category = Category.query.filter_by(id=forum.category.id).first()
    forum = Forum.query.filter_by(id=forum.id).first()

    assert forum is None
    assert category is None


def test_forum_save(category, moderator_user):
    forum = Forum(title="Test Forum", category_id=category.id)
    forum.save()

    assert forum.title == "Test Forum"

    # Test with adding a moderator
    forum.save([moderator_user])

    assert forum.moderators == [moderator_user]


def test_forum_delete(forum):
    forum.delete()

    forum = Forum.query.filter_by(id=forum.id).first()

    assert forum is None


def test_forum_delete_with_user(topic_normal, normal_user):

    assert normal_user.post_count == 1

    topic_normal.forum.delete([normal_user])

    forum = Forum.query.filter_by(id=topic_normal.forum_id).first()

    assert forum is None

    assert normal_user.post_count == 0


def test_forum_update_last_post(topic_normal, normal_user):
    post = Post(content="Test Content 2")
    post.save(topic=topic_normal, user=normal_user)

    assert topic_normal.forum.last_post == post

    post.delete()

    topic_normal.forum.update_last_post()

    assert topic_normal.forum.last_post == topic_normal.first_post


def test_forum_url(forum):
    assert forum.url == "http://localhost:5000/forum/1-test-forum"


def test_forum_slugify(forum):
    assert forum.slug == "test-forum"


def test_topic_save(forum, normal_user):
    post = Post(content="Test Content")
    topic = Topic(title="Test Title")

    assert forum.last_post_id is None
    assert forum.post_count == 0
    assert forum.topic_count == 0

    topic.save(forum=forum, post=post, user=normal_user)

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


def test_topic_delete(topic_normal):
    assert topic_normal.user.post_count == 1
    assert topic_normal.post_count == 1
    assert topic_normal.forum.topic_count == 1
    assert topic_normal.forum.post_count == 1

    topic_normal.delete(users=[topic_normal.user])

    forum = Forum.query.filter_by(id=topic_normal.forum_id).first()
    user = User.query.filter_by(id=topic_normal.user_id).first()
    topic_normal = Topic.query.filter_by(id=topic_normal.id).first()

    assert topic_normal is None
    assert user.post_count == 0
    assert forum.topic_count == 0
    assert forum.post_count == 0
    assert forum.last_post_id is None


def test_topic_merge(topic_normal):
    topic_other = Topic(title="Test Topic Merge")
    post = Post(content="Test Content Merge")
    topic_other.save(post=post, user=topic_normal.user, forum=topic_normal.forum)

    # Save the last_post_id in another variable because topic_other will be
    # overwritten later
    last_post_other = topic_other.last_post_id

    assert topic_other.merge(topic_normal)

    # I just want to be sure that the topic is deleted
    topic_other = Topic.query.filter_by(id=topic_other.id).first()
    assert topic_other is None

    assert topic_normal.post_count == 2
    assert topic_normal.last_post_id == last_post_other


def test_topic_merge_other_forum(topic_normal):
    """You cannot merge a topic with a topic from another forum"""
    forum_other = Forum(title="Test Forum 2", category_id=1)
    forum_other.save()

    topic_other = Topic(title="Test Topic 2")
    post_other = Post(content="Test Content 2")
    topic_other.save(user=topic_normal.user, forum=forum_other, post=post_other)

    assert not topic_normal.merge(topic_other)


def test_topic_move(topic_normal):
    forum_other = Forum(title="Test Forum 2", category_id=1)
    forum_other.save()

    forum_old = Forum.query.filter_by(id=topic_normal.forum_id).first()

    assert topic_normal.move(forum_other)

    assert forum_old.topics == []
    assert forum_old.last_post_id == 0

    assert forum_old.topic_count == 0
    assert forum_old.post_count == 0

    assert forum_other.last_post_id == topic_normal.last_post_id
    assert forum_other.topic_count == 1
    assert forum_other.post_count == 1


def test_topic_move_same_forum(topic_normal):
    assert not topic_normal.move(topic_normal.forum)


def test_topic_update_read():
    # TODO: Refactor it, to make it easier to test it
    pass


def test_topic_url(topic_normal):
    assert topic_normal.url == "http://localhost:5000/topic/1-test-topic-normal"


def test_topic_slug(topic_normal):
    assert topic_normal.slug == "test-topic-normal"


def test_post_save(topic_normal, normal_user):
    post = Post(content="Test Content")
    post.save(topic=topic_normal, user=normal_user)

    assert post.content == "Test Content"

    post.content = "Test Edit Content"
    post.save()

    assert post.content == "Test Edit Content"

    assert topic_normal.user.post_count == 2
    assert topic_normal.post_count == 2
    assert topic_normal.last_post == post
    assert topic_normal.forum.post_count == 2


def test_post_delete(topic_normal):
    post_middle = Post(content="Test Content Middle")
    post_middle.save(topic=topic_normal, user=topic_normal.user)

    post_last = Post(content="Test Content Last")
    post_last.save(topic=topic_normal, user=topic_normal.user)

    assert topic_normal.post_count == 3
    assert topic_normal.forum.post_count == 3
    assert topic_normal.user.post_count == 3

    post_middle.delete()

    # Check the last posts
    assert topic_normal.last_post == post_last
    assert topic_normal.forum.last_post == post_last

    post_last.delete()

    # That was a bit trickier..
    assert topic_normal.post_count == 1
    assert topic_normal.forum.post_count == 1
    assert topic_normal.user.post_count == 1
    assert topic_normal.first_post_id == topic_normal.last_post_id

    assert topic_normal.forum.last_post_id == topic_normal.last_post_id
