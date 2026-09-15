import pytest
from flaskbb.cli.db import downgrade
from flaskbb.extensions import alembic


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
