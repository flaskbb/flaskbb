import sys

import pytest
from flaskbb.cli.bootstrap import bootstrap
from flaskbb.extensions import db
from flaskbb.plugins.models import PluginRegistry
from sqlalchemy.exc import OperationalError

ADMIN = ["--username", "admin", "--email", "admin@example.org", "--password", "test1234"]


@pytest.fixture
def steps(monkeypatch):
    steps = []
    # flaskbb.cli exports the command under the module's name
    monkeypatch.setattr(
        sys.modules["flaskbb.cli.bootstrap"],
        "run_flaskbb",
        lambda description, *args: steps.append(args),
    )
    return steps


def test_installs_into_empty_database(cli_runner, database, steps):
    result = cli_runner.invoke(bootstrap, ADMIN)

    assert result.exit_code == 0, result.output
    assert steps == [("install", "--force", *ADMIN)]


def test_empty_database_without_credentials(cli_runner, database, steps):
    result = cli_runner.invoke(bootstrap, [])

    assert result.exit_code != 0
    assert "no administrator credentials" in result.output
    assert steps == []


def test_migrates_installed_database(cli_runner, user, steps):
    result = cli_runner.invoke(bootstrap, ADMIN)

    assert result.exit_code == 0, result.output
    assert steps == [("db", "upgrade")]


def test_enables_plugins_after_initial_install(cli_runner, database, steps):
    result = cli_runner.invoke(bootstrap, [*ADMIN, "--enable-plugins", "portal, vote,"])

    assert result.exit_code == 0, result.output
    assert steps == [
        ("install", "--force", *ADMIN),
        ("plugins", "enable", "portal"),
        ("plugins", "install", "portal"),
        ("plugins", "enable", "vote"),
        ("plugins", "install", "vote"),
    ]


def test_does_not_enable_plugins_on_later_bootstrap(cli_runner, user, steps):
    PluginRegistry("vote").save()

    result = cli_runner.invoke(bootstrap, ["--enable-plugins", "vote"])

    assert result.exit_code == 0, result.output
    assert steps == [("db", "upgrade")]


def test_does_not_read_plugins_from_environment(cli_runner, database, steps, monkeypatch):
    monkeypatch.setenv("FLASKBB_ENABLE_PLUGINS", "vote")

    result = cli_runner.invoke(bootstrap, ADMIN)

    assert result.exit_code == 0, result.output
    assert steps == [("install", "--force", *ADMIN)]


def test_reads_the_environment(cli_runner, database, steps, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.org")
    monkeypatch.setenv("ADMIN_PASSWORD", "test1234")

    result = cli_runner.invoke(bootstrap, [])

    assert result.exit_code == 0, result.output
    assert steps == [("install", "--force", *ADMIN)]


def test_wait_only(cli_runner, database, steps):
    result = cli_runner.invoke(bootstrap, ["--wait-only"])

    assert result.exit_code == 0, result.output
    assert steps == []


def test_gives_up_on_unreachable_database(cli_runner, database, steps, monkeypatch):
    def refuse():
        raise OperationalError("connect", None, Exception("connection refused"))

    monkeypatch.setattr(db.engine, "connect", refuse)

    result = cli_runner.invoke(bootstrap, ["--timeout", "0"])

    assert result.exit_code != 0
    assert "isn't reachable after 0s" in result.output
    assert steps == []
