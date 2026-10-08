import pytest
from flaskbb.cli.db import downgrade, upgrade
from flaskbb.extensions import alembic


@pytest.mark.parametrize(
    ("arguments", "target"),
    [
        (["1789335000"], "1789335000"),
        (["2"], "+2"),
        (["+2"], "+2"),
        (["9"], "+9"),
        ([], "heads"),
        (["portal@head"], "portal@head"),
    ],
)
def test_upgrade_tells_revision_ids_and_step_counts_apart(
    cli_runner, monkeypatch, arguments, target
):
    calls = []
    monkeypatch.setattr(
        alembic, "upgrade", lambda target, skip_missing: calls.append((target, skip_missing))
    )

    result = cli_runner.invoke(upgrade, arguments, obj=alembic)

    assert result.exit_code == 0, result.output
    assert calls == [(target, False)]


def test_upgrade_skips_missing_revisions_on_request(cli_runner, monkeypatch):
    calls = []
    monkeypatch.setattr(
        alembic, "upgrade", lambda target, skip_missing: calls.append((target, skip_missing))
    )

    result = cli_runner.invoke(upgrade, ["--skip-missing"], obj=alembic)

    assert result.exit_code == 0, result.output
    assert calls == [("heads", True)]


@pytest.mark.parametrize(
    ("arguments", "target"),
    [
        (["1789335000"], "1789335000"),
        (["2"], "-2"),
        (["--", "-2"], "-2"),
        (["9"], "-9"),
        ([], "-1"),
        (["portal@base"], "portal@base"),
    ],
)
def test_downgrade_tells_revision_ids_and_step_counts_apart(
    cli_runner, monkeypatch, arguments, target
):
    targets = []
    monkeypatch.setattr(alembic, "downgrade", targets.append)

    result = cli_runner.invoke(downgrade, arguments, obj=alembic)

    assert result.exit_code == 0, result.output
    assert targets == [target]
