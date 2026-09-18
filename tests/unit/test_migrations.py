import importlib.util
import os
import sys
from importlib.metadata import EntryPoint
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from flaskbb.app import configure_migrations
from flaskbb.extensions import alembic, db, pluggy
from flaskbb.plugins.utils import plugins_with_pending_migrations


def _load_migration(filename):
    path = Path(__file__).parents[2] / "flaskbb" / "migrations" / filename
    spec = importlib.util.spec_from_file_location(f"_migration_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_disabled_plugin_migrations_are_loaded_without_importing_the_plugin(
    application, monkeypatch, tmp_path
):
    plugin_dir = tmp_path / "disabled_plugin"
    (plugin_dir / "migrations").mkdir(parents=True)
    (plugin_dir / "__init__.py").write_text("raise RuntimeError('must not be imported')\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(
        pluggy,
        "list_disabled_plugins",
        lambda: [
            EntryPoint(name="disabled_plugin", value="disabled_plugin", group="flaskbb_plugins")
        ],
    )
    monkeypatch.setitem(application.config, "ALEMBIC", dict(application.config["ALEMBIC"]))

    configure_migrations(application)

    migrations = str(plugin_dir / "migrations")
    assert ("disabled_plugin", migrations) in application.config["ALEMBIC"]["version_locations"]
    assert application.config["ALEMBIC"]["disabled_version_locations"] == [migrations]
    assert "disabled_plugin" not in sys.modules


PLUGIN_MIGRATION = """
revision = "f00dfeed0001"
down_revision = None
branch_labels = ("pending_plugin",)
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
"""


@pytest.fixture
def pending_plugin(monkeypatch, tmp_path):
    plugin_dir = tmp_path / "pending_plugin"
    (plugin_dir / "migrations").mkdir(parents=True)
    (plugin_dir / "migrations" / "f00dfeed0001_init.py").write_text(PLUGIN_MIGRATION)
    (plugin_dir / "__init__.py").write_text("raise RuntimeError('must not be imported')\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    return EntryPoint(name="pending_plugin", value="pending_plugin", group="flaskbb_plugins")


@pytest.fixture
def alembic_version(database):
    db.session.execute(
        sa.text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)")
    )
    db.session.commit()

    yield

    db.session.execute(sa.text("DROP TABLE alembic_version"))
    db.session.commit()


def test_plugin_with_pending_migrations_is_held_back(application, database, pending_plugin):
    held_back = plugins_with_pending_migrations(application, [pending_plugin], {"pending_plugin"})

    assert held_back == {"pending_plugin"}
    assert "pending_plugin" not in sys.modules


def test_only_enabled_plugins_are_held_back(application, database, pending_plugin):
    assert plugins_with_pending_migrations(application, [pending_plugin], {"other"}) == set()


def test_plugin_with_applied_migrations_is_loaded(application, alembic_version, pending_plugin):
    db.session.execute(sa.text("INSERT INTO alembic_version VALUES ('f00dfeed0001')"))
    db.session.commit()

    held_back = plugins_with_pending_migrations(application, [pending_plugin], {"pending_plugin"})

    assert held_back == set()


def test_held_back_plugin_migrations_run_with_upgrade_heads(
    application, monkeypatch, pending_plugin
):
    monkeypatch.setattr(pluggy, "list_disabled_plugins", lambda: [pending_plugin])
    monkeypatch.setitem(application.extensions, "flaskbb_held_back_plugins", {"pending_plugin"})
    monkeypatch.setitem(application.config, "ALEMBIC", dict(application.config["ALEMBIC"]))

    configure_migrations(application)

    assert application.config["ALEMBIC"]["disabled_version_locations"] == []
    assert any(
        name == "pending_plugin" for name, _ in application.config["ALEMBIC"]["version_locations"]
    )


def test_upgrade_heads_leaves_out_disabled_plugin_migrations(application, monkeypatch):
    migrations = os.path.join(pluggy.get_plugin_path("conversations"), "migrations")
    monkeypatch.setitem(application.config["ALEMBIC"], "disabled_version_locations", [migrations])
    planned = []
    monkeypatch.setattr(
        alembic,
        "run_migrations",
        lambda fn: planned.extend(step.revision.path for step in fn((), None)),
    )

    alembic.upgrade()

    assert planned
    assert not [path for path in planned if path.startswith(migrations)]

    planned.clear()
    alembic.upgrade("conversations@head")

    assert [path for path in planned if path.startswith(migrations)]


def test_plugin_registry_enabled_migration_disables_null_rows(database):
    migration = _load_migration(
        "202609132130_1789335000_widen_user_password_and_not_null_columns.py"
    )
    context = MigrationContext.configure(db.session.connection())
    with Operations(context).batch_alter_table("plugin_registry") as batch_op:
        batch_op.alter_column("enabled", existing_type=sa.Boolean(), nullable=True)
    db.session.execute(
        sa.text("INSERT INTO plugin_registry (name, enabled) VALUES ('old_plugin', NULL)")
    )

    with Operations.context(context):
        migration.upgrade()
    db.session.commit()

    enabled = db.session.execute(
        sa.text("SELECT enabled FROM plugin_registry WHERE name = 'old_plugin'")
    ).scalar_one()
    column = next(
        c for c in sa.inspect(db.engine).get_columns("plugin_registry") if c["name"] == "enabled"
    )
    assert enabled == 0
    assert column["nullable"] is False


def test_hidden_and_post_count_migration_fills_null_rows(user):
    migration = _load_migration(
        "202609132130_1789335000_widen_user_password_and_not_null_columns.py"
    )
    context = MigrationContext.configure(db.session.connection())
    with Operations(context).batch_alter_table("users") as batch_op:
        batch_op.alter_column("post_count", existing_type=sa.Integer(), nullable=True)
    db.session.execute(sa.text("UPDATE users SET post_count = NULL"))

    with Operations.context(context):
        migration.upgrade()
    db.session.commit()

    post_count = db.session.execute(sa.text("SELECT post_count FROM users")).scalar_one()
    columns = {c["name"]: c for c in sa.inspect(db.engine).get_columns("users")}
    assert post_count == 0
    assert columns["post_count"]["nullable"] is False


def test_attachment_filename_index_matches_the_migration(database):
    indexes = [
        (index["name"], index["column_names"], bool(index["unique"]))
        for index in sa.inspect(db.engine).get_indexes("attachments")
    ]

    assert ("ix_attachments_filename", ["filename"], True) in indexes
