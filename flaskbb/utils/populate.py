"""
flaskbb.utils.populate
~~~~~~~~~~~~~~~~~~~~~~

A module that makes creating data more easily

:copyright: (c) 2014 by the FlaskBB Team.
:license: BSD, see LICENSE for more details.
"""

import logging
import os
from typing import Any

from alembic.util.exc import CommandError
from sqlalchemy import func, select
from sqlalchemy_utils.functions import (  # pyright: ignore[reportUnknownVariableType]
    create_database,
    database_exists,
)

from flaskbb.core.settings import Setting, setting_registry
from flaskbb.extensions import alembic, db, pluggy
from flaskbb.forum.models import Category, Forum, Post, Topic
from flaskbb.user.models import Group, User

logger = logging.getLogger(__name__)


def create_default_settings() -> None:
    """Populates the settings table for every registered SettingGroup
    (core + plugins).

    Call site change: the old create_default_settings() took no
    arguments; this one needs the app's plugin manager so it can call
    registry.load_from_plugins() before seeding, e.g. in the `install`
    CLI command:

        create_default_settings(app.pluggy)
    """
    for group in setting_registry.all_groups():
        Setting.install_group(group.key)


def update_settings_from_fixture(group_key: str | None = None, force: bool = False) -> None:
    """Re-applies default values from the registry to the settings
    table - the `flaskbb upgrade` CLI command's underlying logic.

    :param group_key: limit to a single group (e.g. "general"); None
        updates every registered group.
    :param force: WARNING - this overwrites existing values back to
        their defaults, discarding whatever an admin has configured.
        Without this, only rows that don't exist yet are created,
        matching the CLI's default (non---force) behavior.
    """
    groups = [setting_registry.group(group_key)] if group_key else setting_registry.all_groups()
    for group in groups:
        if force:
            Setting.remove_group(group.key)
        Setting.install_group(group.key)


def delete_settings_from_fixture(group_key: str | None = None) -> None:
    """Deletes settings rows whose definitions no longer exist in the
    registry.

    :param group_key: limit to a single group (e.g. "general"); None
        checks every registered group.
    """
    groups = [setting_registry.group(group_key)] if group_key else setting_registry.all_groups()
    for group in groups:
        valid_keys_lower = {s.key.lower() for s in group.settings}
        existing_rows = db.session.execute(
            select(Setting).where(Setting.group_key == group.key)
        ).scalars()
        for row in existing_rows:
            if row.key.lower() not in valid_keys_lower:
                db.session.delete(row)

    db.session.commit()
    Setting.invalidate_cache()


def create_default_groups():
    """This will create the 5 default groups."""
    from flaskbb.fixtures.groups import fixture

    result: list[Group] = []
    for key, value in fixture.items():
        group = Group(name=key)

        for k, v in value.items():
            setattr(group, k, v)

        group.save()
        result.append(group)
    return result


def create_user(username: str, password: str, email: str, groupname: str):
    """Creates a user.
    Returns the created user.

    :param username: The username of the user.
    :param password: The password of the user.
    :param email: The email address of the user.
    :param groupname: The name of the group to which the user
                      should belong to.
    """
    if groupname == "member":
        group = Group.get_member_group()
    else:
        group = db.session.execute(
            select(Group)
            .filter(getattr(Group, groupname).is_(True))
            .order_by(Group.id.asc())
            .limit(1)
        ).scalar_one()

    user = User.create(
        username=username,
        password=password,
        email=email,
        primary_group_id=group.id,
        activated=True,
    )
    return user


def update_user(
    username: str,
    password: str | None,
    email: str | None,
    groupname: str | None,
):
    """Update an existing user. Only the fields that are not ``None`` are
    updated.
    Returns the updated user.

    :param username: The username of the user.
    :param password: The password of the user.
    :param email: The email address of the user.
    :param groupname: The name of the group to which the user
                      should belong to.
    """
    user = db.session.execute(select(User).filter_by(username=username)).scalar_one_or_none()
    if user is None:
        return None

    if password is not None:
        user.password = password
    if email is not None:
        user.email = email
    if groupname is not None:
        if groupname == "member":
            group = Group.get_member_group()
        else:
            group = db.session.execute(
                select(Group)
                .filter(getattr(Group, groupname).is_(True))
                .order_by(Group.id.asc())
                .limit(1)
            ).scalar_one()
        user.primary_group_id = group.id
    return user.save()


def create_welcome_forum():
    """This will create the `welcome forum` with a welcome topic.
    Returns True if it's created successfully.
    """
    user_count = db.session.execute(db.select(func.count()).select_from(User)).scalar_one()
    if user_count < 1:
        return False

    user = db.session.execute(select(User).filter_by(id=1)).scalar_one_or_none()

    category = Category(title="My Category", position=1)
    category.save()

    forum = Forum(title="Welcome", description="Your first forum", category_id=category.id)
    forum.save()

    topic = Topic(title="Welcome!")
    post = Post(content="Have fun with your new FlaskBB Forum!")

    topic.save(user=user, forum=forum, post=post)
    return True


def create_test_data(
    categories: int = 1,
    forums: int = 1,
    topics: int = 1,
    posts: int = 2,
):
    """Creates one user for each default group except the guest group, some
    categories with forums in them and, in each forum, topics for every user
    with replies from a different user.
    Returns the amount of created users, categories, forums, topics and posts
    as a dict.

    :param categories: The number of categories.
    :param forums: The number of forums which are created in each category.
    :param topics: The number of topics which are created for each user in
                   each forum.
    :param posts: The number of replies which are created in each topic.
    """
    groups = create_default_groups()
    create_default_settings()

    data_created = {"users": 0, "categories": 0, "forums": 0, "topics": 0, "posts": 0}

    # create one user per group - a guest can't create topics or posts
    users: list[User] = []
    for group in groups:
        if group.guest:
            continue

        username = group.name.lower().replace(" ", "_")
        email = f"{username}@example.org"
        user = User(username=username, password="test", email=email)
        user.primary_group_id = group.id
        user.activated = True
        user.save()
        users.append(user)
        data_created["users"] += 1

    with db.session.no_autoflush:
        for i in range(1, categories + 1):
            category_title = f"Test Category {i}"
            category = Category(title=category_title, description="Test Description")
            category.save()
            data_created["categories"] += 1

            for j in range(1, forums + 1):
                forum_title = f"Test Forum {j} {i}"
                forum = Forum(
                    title=forum_title,
                    description="Test Description",
                    category_id=category.id,
                )
                forum.save()
                data_created["forums"] += 1

                for k in range(1, topics + 1):
                    for index, user in enumerate(users):
                        # the replies are written by the next user in the list
                        other_user = users[(index + 1) % len(users)]

                        topic = Topic(title=f"Test Title {k} from {user.username}")
                        post = Post(content="Test Content")
                        topic.save(user=user, forum=forum, post=post)
                        data_created["topics"] += 1

                        for _ in range(1, posts + 1):
                            post = Post(content="Test Post")
                            post.save(user=other_user, topic=topic)
                            data_created["posts"] += 1

    return data_created


def insert_bulk_data(topic_count: int = 10, post_count: int = 100):
    """Creates a specified number of topics in the first forum with
    each topic containing a specified amount of posts.
    Returns the number of created topics and posts.

    :param topics: The amount of topics in the forum.
    :param posts: The number of posts in each topic.
    """
    user1 = db.session.execute(select(User).where(User.id == 1)).scalar()
    user2 = db.session.execute(select(User).where(User.id == 2)).scalar()
    forum = db.session.execute(select(Forum).where(Forum.id == 1)).scalar()

    last_post = db.session.execute(select(Post).order_by(Post.id.desc())).scalar()
    last_post_id = 1 if last_post is None else last_post.id

    created_posts = 0
    created_topics = 0
    posts: list[Post] = []

    if not (user1 and user2 and forum):
        return False

    with db.session.no_autoflush:
        for i in range(1, topic_count + 1):
            last_post_id += 1

            # create a topic
            topic = Topic(title=f"Test Title {i}")
            post = Post(content="First Post")
            topic.save(post=post, user=user1, forum=forum)
            created_topics += 1

            # create some posts in the topic
            for _ in range(1, post_count + 1):
                last_post_id += 1
                post = Post(content="Some other Post", user=user2, topic=topic.id)
                topic.last_updated = post.date_created
                topic.post_count += 1

                created_posts += 1
                posts.append(post)

        db.session.bulk_save_objects(posts)

    # and finally, lets update some stats
    forum.recalculate(last_post=True)
    user1.recalculate()
    user2.recalculate()

    return created_topics, created_posts


def create_latest_db(target: str = "default@head"):
    """Creates the database including the schema using SQLAlchemy's
    db.create_all method instead of going through all the database revisions.
    The revision will be set to 'head' which indicates the latest alembic
    revision.

    :param target: The target branch. Defaults to 'default@head'.
    """
    if not database_exists(db.engine.url):
        create_database(db.engine.url)

    db.create_all()
    alembic.stamp(target=target)


def has_migrations(plugin: Any):
    migrations_path = os.path.join(plugin.__path__[0], "migrations")
    if os.path.exists(migrations_path) and len(os.listdir(migrations_path)) != 0:
        return True
    return False


def run_plugin_migrations(plugins: list[str] | None = None):
    """Runs the migrations for a list of plugins.

    :param plugins: A iterable of plugin names to run the migrations for. If set
                    to ``None``, all external plugin migrations will be run.
    """
    all_plugins: list[str | None] | list[str] = []
    if plugins is None:
        all_plugins = [pluggy.get_name(p) for p in pluggy.get_external_plugins()]
    else:
        all_plugins = plugins

    for plugin_name in all_plugins:
        if plugin_name is None:
            continue

        plugin = pluggy.get_plugin(plugin_name)

        if not has_migrations(plugin):
            logger.debug(f"No migrations found for plugin {plugin_name}")
            continue

        try:
            alembic.upgrade(target=f"{plugin_name}@head")
        except CommandError as exc:
            logger.debug(
                f"Couldn't run migrations for plugin {plugin_name} because of "
                "following exception: ",
                exc_info=exc,
            )
