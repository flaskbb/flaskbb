from flaskbb.cli.users import (
    activate_user,
    add_to_group,
    ban_user,
    deactivate_user,
    list_users,
    remove_from_group,
    set_primary_group,
    show_user,
    unban_user,
)
from flaskbb.extensions import db
from flaskbb.user.models import User


def test_list_users(cli_runner, user, admin_user):
    result = cli_runner.invoke(list_users, [])

    assert result.exit_code == 0
    assert "test_normal" in result.output
    assert "test_admin" in result.output


def test_list_users_filtered_by_group(cli_runner, user, admin_user):
    result = cli_runner.invoke(list_users, ["--group", "administrator"])

    assert result.exit_code == 0
    assert "test_admin" in result.output
    assert "test_normal" not in result.output


def test_list_users_filtered_by_banned(cli_runner, user, default_groups):
    user.primary_group = default_groups[4]
    user.save()

    result = cli_runner.invoke(list_users, ["--banned"])

    assert result.exit_code == 0
    assert "test_normal" in result.output


def test_list_users_filtered_by_unactivated(cli_runner, user, unactivated_user):
    result = cli_runner.invoke(list_users, ["--unactivated"])

    assert result.exit_code == 0
    assert "notactive" in result.output
    assert "test_normal" not in result.output


def test_list_users_without_matches(cli_runner, default_groups):
    result = cli_runner.invoke(list_users, [])

    assert result.exit_code == 0
    assert "No users found" in result.output


def test_show_user(cli_runner, user, default_groups):
    user.add_to_group(default_groups[2])
    user.save()

    result = cli_runner.invoke(show_user, ["test_normal"])

    assert result.exit_code == 0
    assert "test_normal@example.org" in result.output
    assert "Moderator" in result.output
    # granted by the secondary moderator group
    assert "mod_banuser" in result.output


def test_show_unknown_user(cli_runner, default_groups):
    result = cli_runner.invoke(show_user, ["nobody"])

    assert result.exit_code != 0
    assert "does not exist" in result.stderr


def test_ban_and_unban_user(cli_runner, user, default_groups):
    result = cli_runner.invoke(ban_user, ["test_normal"])

    assert result.exit_code == 0
    assert user.primary_group.banned

    result = cli_runner.invoke(unban_user, ["test_normal"])

    assert result.exit_code == 0
    assert not user.primary_group.banned


def test_ban_banned_user(cli_runner, user, default_groups):
    user.primary_group = default_groups[4]
    user.save()

    result = cli_runner.invoke(ban_user, ["test_normal"])

    assert result.exit_code != 0
    assert "already banned" in result.stderr


def test_unban_unbanned_user(cli_runner, user):
    result = cli_runner.invoke(unban_user, ["test_normal"])

    assert result.exit_code != 0
    assert "is not banned" in result.stderr


def test_activate_and_deactivate_user(cli_runner, unactivated_user):
    result = cli_runner.invoke(activate_user, ["notactive"])

    assert result.exit_code == 0
    assert unactivated_user.activated

    result = cli_runner.invoke(deactivate_user, ["notactive"])

    assert result.exit_code == 0
    assert not unactivated_user.activated


def test_activate_activated_user(cli_runner, user):
    result = cli_runner.invoke(activate_user, ["test_normal"])

    assert result.exit_code != 0
    assert "already activated" in result.stderr


def test_set_primary_group(cli_runner, user, default_groups):
    result = cli_runner.invoke(set_primary_group, ["test_normal", "Moderator"])

    assert result.exit_code == 0
    assert user.primary_group.name == "Moderator"


def test_set_primary_group_moves_it_out_of_the_secondary_groups(cli_runner, user, default_groups):
    user.add_to_group(default_groups[2])
    user.save()

    result = cli_runner.invoke(set_primary_group, ["test_normal", "Moderator"])

    assert result.exit_code == 0
    assert user.primary_group.name == "Moderator"
    assert user.secondary_groups.count() == 0


def test_set_primary_group_to_the_current_one(cli_runner, user, default_groups):
    result = cli_runner.invoke(set_primary_group, ["test_normal", "Member"])

    assert result.exit_code != 0
    assert "already is the primary group" in result.stderr


def test_add_and_remove_group(cli_runner, user, default_groups):
    result = cli_runner.invoke(add_to_group, ["test_normal", "Moderator"])

    assert result.exit_code == 0
    assert [group.name for group in user.secondary_groups] == ["Moderator"]

    result = cli_runner.invoke(remove_from_group, ["test_normal", "Moderator"])

    assert result.exit_code == 0
    assert user.secondary_groups.count() == 0


def test_add_group_twice(cli_runner, user, default_groups):
    user.add_to_group(default_groups[2])
    user.save()

    result = cli_runner.invoke(add_to_group, ["test_normal", "Moderator"])

    assert result.exit_code != 0
    assert "already is in the group" in result.stderr


def test_add_primary_group_as_secondary_group(cli_runner, user, default_groups):
    result = cli_runner.invoke(add_to_group, ["test_normal", "Member"])

    assert result.exit_code != 0
    assert "already is the primary group" in result.stderr


def test_remove_group_the_user_is_not_in(cli_runner, user, default_groups):
    result = cli_runner.invoke(remove_from_group, ["test_normal", "Moderator"])

    assert result.exit_code != 0
    assert "is not in the group" in result.stderr


def test_group_membership_survives_a_reload(cli_runner, user, default_groups):
    cli_runner.invoke(add_to_group, ["test_normal", "Moderator"])

    reloaded = db.session.execute(db.select(User).filter_by(username="test_normal")).scalar_one()
    assert [group.name for group in reloaded.secondary_groups] == ["Moderator"]
