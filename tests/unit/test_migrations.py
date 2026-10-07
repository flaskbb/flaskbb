import importlib.util
import os
import sys
from importlib.metadata import EntryPoint
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from alembic.util.exc import CommandError
from flask_alembic import Alembic as FlaskAlembic
from flaskbb.app import configure_migrations
from flaskbb.extensions import alembic, db, pluggy
from flaskbb.permissions import PermissionLevel
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
    monkeypatch.setitem(application.config, "MIGRATIONS_DISABLED_VERSION_LOCATIONS", [])

    configure_migrations(application)

    migrations = str(plugin_dir / "migrations")
    assert ("disabled_plugin", migrations) in application.config["ALEMBIC"]["version_locations"]
    assert application.config["MIGRATIONS_DISABLED_VERSION_LOCATIONS"] == [migrations]
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
    monkeypatch.setitem(application.config, "MIGRATIONS_DISABLED_VERSION_LOCATIONS", [])

    configure_migrations(application)

    assert application.config["MIGRATIONS_DISABLED_VERSION_LOCATIONS"] == []
    assert any(
        name == "pending_plugin" for name, _ in application.config["ALEMBIC"]["version_locations"]
    )


def test_upgrade_heads_leaves_out_disabled_plugin_migrations(application, monkeypatch):
    migrations = os.path.join(pluggy.get_plugin_path("conversations"), "migrations")
    monkeypatch.setitem(application.config, "MIGRATIONS_DISABLED_VERSION_LOCATIONS", [migrations])
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


@pytest.fixture
def second_plugin_branch(application, monkeypatch, pending_plugin):
    monkeypatch.setattr(pluggy, "list_disabled_plugins", lambda: [pending_plugin])
    monkeypatch.setitem(application.config, "ALEMBIC", dict(application.config["ALEMBIC"]))
    monkeypatch.setitem(application.config, "MIGRATIONS_DISABLED_VERSION_LOCATIONS", [])
    configure_migrations(application)
    monkeypatch.setattr(alembic._get_cache(), "config", None)
    monkeypatch.setattr(alembic._get_cache(), "script", None)


@pytest.fixture
def created(monkeypatch):
    calls = []
    monkeypatch.setattr(FlaskAlembic, "revision", lambda self, *args: calls.append(args))
    monkeypatch.setattr(FlaskAlembic, "merge", lambda self, *args: calls.append(args))
    return calls


def test_plugin_revision_can_not_depend_on_another_plugin(application, created):
    with pytest.raises(CommandError, match="conversations"):
        alembic.revision("add column", empty=True, branch="portal", depend=["1785520254"])

    with pytest.raises(CommandError, match="conversations"):
        alembic.revision("add column", empty=True, branch="portal", parent=["conversations@head"])

    assert created == []


def test_core_revision_can_not_depend_on_a_plugin(application, created):
    with pytest.raises(CommandError, match="conversations"):
        alembic.revision("add column", empty=True, depend=["1785520254"])

    assert created == []


def test_plugin_revision_can_depend_on_core_and_its_own_branch(application, created):
    alembic.revision(
        "add column", empty=True, branch="conversations", depend=["1783713047", "1770409336"]
    )

    assert len(created) == 1


def test_merge_can_not_join_plugins(application, second_plugin_branch, created):
    with pytest.raises(CommandError, match="conversations, pending_plugin"):
        alembic.merge(["conversations@head", "pending_plugin@head"])

    alembic.merge(["conversations@head", "default@head"])

    assert len(created) == 1


@pytest.mark.parametrize("old_install", [False, True])
def test_group_roles_migration_moves_flags_and_permissions_to_rows(database, old_install):
    """FlaskBB 2.x installs carry a CHECK constraint per boolean column, which
    SQLite can only drop by rebuilding the table; newer ones drop in place.
    """
    migration = _load_migration("202610061554_1791294853_group_roles_and_permissions.py")
    connection = db.session.connection()
    # the migration runner suspends foreign keys for the batch rebuild (see
    # flaskbb.utils.alembic); calling the migration directly has to as well,
    # or dropping the rebuilt groups table cascades into group_permissions
    connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
    try:
        context = MigrationContext.configure(connection)
        operations = Operations(context)
        operations.drop_table("group_permissions")
        operations.drop_column("groups", "role")
        for name in migration.ROLE_FLAGS + migration.PERMISSIONS:
            check = f" CHECK ({name} IN (0, 1))" if old_install else ""
            connection.exec_driver_sql(
                f"ALTER TABLE groups ADD COLUMN {name} BOOLEAN NOT NULL DEFAULT 0{check}"
            )
        db.session.execute(
            sa.text(
                "INSERT INTO groups (name, mod, editpost, viewhidden) VALUES ('Old Mods', 1, 1, 1)"
            )
        )

        with Operations.context(context):
            migration.upgrade()
        db.session.commit()

        role = db.session.execute(
            sa.text("SELECT role FROM groups WHERE name = 'Old Mods'")
        ).scalar_one()
        granted = dict(
            db.session.execute(sa.text("SELECT permission, granted FROM group_permissions")).all()
        )
        inspector = sa.inspect(db.engine)
        columns = {c["name"] for c in inspector.get_columns("groups")}
        checks = inspector.get_check_constraints("groups")
        db.session.commit()
    finally:
        # the commit released the connection above; the pooled one stays
        # switched off otherwise, as the connect listener does not run again
        db.session.connection().exec_driver_sql("PRAGMA foreign_keys=ON")
        db.session.commit()

    assert role == "mod"
    assert granted["editpost"] == 1
    assert granted["viewhidden"] == 1
    assert granted["deletepost"] == 0
    assert set(migration.PERMISSIONS) == set(granted)
    assert columns.isdisjoint(migration.ROLE_FLAGS + migration.PERMISSIONS)
    assert checks == []


def test_group_permission_levels_migration_round_trips(default_groups):
    migration = _load_migration("202610070930_1791358200_group_permission_levels.py")
    member = default_groups[3]
    member.set_permission("deletepost", PermissionLevel.NEVER)
    member.save()
    context = MigrationContext.configure(db.session.connection())

    with Operations.context(context):
        migration.downgrade()
    db.session.commit()
    granted = dict(
        db.session.execute(
            sa.text("SELECT permission, granted FROM group_permissions WHERE group_id = :id"),
            {"id": member.id},
        ).all()
    )
    assert granted["editpost"] == 1
    assert granted["makehidden"] == 0
    assert granted["deletepost"] == 0

    context = MigrationContext.configure(db.session.connection())
    with Operations.context(context):
        migration.upgrade()
    db.session.commit()
    levels = dict(
        db.session.execute(
            sa.text("SELECT permission, level FROM group_permissions WHERE group_id = :id"),
            {"id": member.id},
        ).all()
    )
    assert levels["editpost"] == "allow"
    assert levels["makehidden"] == "deny"
    assert levels["deletepost"] == "deny"
    columns = {c["name"] for c in sa.inspect(db.engine).get_columns("group_permissions")}
    assert columns == {"group_id", "permission", "level"}
