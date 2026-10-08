from click.testing import CliRunner
from flaskbb.cli.main import flaskbb
from flaskbb.extensions import alembic


def test_a_missing_config_fails_instead_of_falling_back(monkeypatch, tmp_path):
    upgrades = []
    monkeypatch.setattr(alembic, "upgrade", lambda *args, **kwargs: upgrades.append(args))
    missing = str(tmp_path / "missing.cfg")
    # FlaskGroup sets FLASK_RUN_FROM_CLI, the runner unsets it again afterwards
    runner = CliRunner(env={"FLASK_RUN_FROM_CLI": None, "FLASKBB_SETTINGS": None})

    result = runner.invoke(flaskbb, ["--config", missing, "db", "upgrade"])

    assert result.exit_code == 1, result.output
    assert (
        f"Error: Config {missing!r} is neither an existing file nor an importable object."
        in result.output
    )
    assert upgrades == []
