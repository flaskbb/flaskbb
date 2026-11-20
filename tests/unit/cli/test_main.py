import pytest
from click.testing import CliRunner
from flaskbb.cli import main
from flaskbb.cli.main import flaskbb
from flaskbb.core.exceptions import InsecureSecretKeyError
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


@pytest.mark.parametrize(
    ("command", "checked"),
    [("run", True), ("serve", True), ("urls", False), ("makeconfig", False), ("celery", False)],
)
def test_only_the_serving_commands_check_the_secret_key(monkeypatch, command, checked):
    checks = []

    def create_app(config, instance_path, check_secret_key):
        checks.append(check_secret_key)
        raise InsecureSecretKeyError("SECRET_KEY is not set")

    monkeypatch.setattr(main, "create_app", create_app)
    monkeypatch.setattr(flaskbb, "_loaded_flaskbb_plugins", False)
    runner = CliRunner(env={"FLASK_RUN_FROM_CLI": None})

    result = runner.invoke(flaskbb, [command])

    assert result.exit_code == 1, result.output
    assert "Error: SECRET_KEY is not set" in result.output
    assert checks == [checked]
