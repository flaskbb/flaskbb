from flaskbb.cli.permissions import list_permissions, set_permission, show_permissions


def test_list_permissions(cli_runner, default_groups):
    result = cli_runner.invoke(list_permissions, [])

    assert result.exit_code == 0
    assert "Administrator" in result.output
    assert "Guest" in result.output
    assert "makehidden" in result.output


def test_list_permissions_of_a_single_group(cli_runner, default_groups):
    result = cli_runner.invoke(list_permissions, ["--group", "Member"])

    assert result.exit_code == 0
    assert "Member" in result.output
    assert "Administrator" not in result.output


def test_show_permissions(cli_runner, user, default_groups):
    user.add_to_group(default_groups[2])
    user.save()

    result = cli_runner.invoke(show_permissions, ["test_normal"])

    assert result.exit_code == 0
    assert "Groups: Member, Moderator" in result.output
    rows = {line.split()[0]: line.split(maxsplit=1)[1] for line in result.output.splitlines()[4:]}
    # granted by the moderator group only
    assert rows["mod_banuser"].split() == ["yes", "Moderator"]
    # granted by both groups
    assert rows["editpost"].split() == ["yes", "Member,", "Moderator"]
    assert rows["makehidden"].split() == ["no", "-"]


def test_set_permission(cli_runner, default_groups):
    result = cli_runner.invoke(set_permission, ["Member", "deletepost", "true"])

    assert result.exit_code == 0
    assert default_groups[3].deletepost

    result = cli_runner.invoke(set_permission, ["member", "deletepost", "false"])

    assert result.exit_code == 0
    assert not default_groups[3].deletepost


def test_set_unknown_permission(cli_runner, default_groups):
    result = cli_runner.invoke(set_permission, ["Member", "flyaround", "true"])

    assert result.exit_code != 0
    assert "Unknown permission: flyaround" in result.stderr


def test_set_permission_of_unknown_group(cli_runner, default_groups):
    result = cli_runner.invoke(set_permission, ["Nobodies", "deletepost", "true"])

    assert result.exit_code != 0
    assert "does not exist" in result.stderr


def test_set_permission_invalidates_the_cached_permissions(cli_runner, user, default_groups):
    assert not user.permissions["deletepost"]

    result = cli_runner.invoke(set_permission, ["Member", "deletepost", "true"])

    assert result.exit_code == 0
    assert user.permissions["deletepost"]
