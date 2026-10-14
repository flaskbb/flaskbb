import importlib
import types

import pytest
import sqlalchemy as sa
from alembic.util.exc import CommandError
from flask_login import login_user
from flaskbb.app import upgrade_installed_plugin_settings
from flaskbb.extensions import db, pluggy
from flaskbb.management import views
from flaskbb.permissions import PermissionLevel
from flaskbb.plugins import utils
from flaskbb.plugins.models import PluginRegistry
from flaskbb.settings.definitions import IntSetting, SettingGroup
from flaskbb.settings.models import Setting
from flaskbb.settings.registry import setting_registry
from flaskbb.user.models import GroupPermission

# flaskbb.cli.plugins is shadowed by the click group of the same name
cli_plugins = importlib.import_module("flaskbb.cli.plugins")


@pytest.fixture
def dummy_plugin():
    module = types.ModuleType("dummy_plugin")
    pluggy.register(module, "dummy_plugin")

    yield module

    pluggy.unregister(module)


@pytest.fixture
def dummy_registry(database, dummy_plugin):
    registry = PluginRegistry("dummy_plugin")
    registry.enabled = False
    return registry.save()


@pytest.fixture
def dummy_settings(dummy_plugin):
    group = SettingGroup(
        key="dummy_plugin",
        name="Dummy",
        description="Dummy settings",
        settings=(
            IntSetting(key="OLD", value=1, name="Old", description="Installed setting"),
            IntSetting(key="NEW", value=2, name="New", description="Added by an update"),
        ),
    )
    setting_registry.register_group(group, is_plugin=True)

    yield group

    setting_registry.unregister_group(group.key)


@pytest.fixture
def migrations(monkeypatch):
    applied: list[str] = []

    def apply(name: str) -> bool:
        applied.append(name)
        return True

    monkeypatch.setattr(views, "apply_plugin_migrations", apply)
    monkeypatch.setattr(cli_plugins, "apply_plugin_migrations", apply)
    return applied


@pytest.fixture
def failing_migrations(monkeypatch):
    def apply(name: str) -> bool:
        raise CommandError("boom")

    monkeypatch.setattr(views, "apply_plugin_migrations", apply)
    monkeypatch.setattr(cli_plugins, "apply_plugin_migrations", apply)


@pytest.fixture
def reverted(monkeypatch):
    reverted: list[str] = []

    def revert(name: str) -> bool:
        reverted.append(name)
        return True

    monkeypatch.setattr(views, "revert_plugin_migrations", revert)
    monkeypatch.setattr(cli_plugins, "revert_plugin_migrations", revert)
    return reverted


@pytest.fixture
def removed_settings(monkeypatch):
    removed: list[str] = []
    monkeypatch.setattr(PluginRegistry, "remove_settings", lambda self: removed.append(self.name))
    return removed


@pytest.fixture
def applied_migrations(monkeypatch):
    monkeypatch.setattr(utils, "plugin_has_applied_migrations", lambda name: True)
    monkeypatch.setattr(views, "plugin_has_applied_migrations", lambda name: True)
    monkeypatch.setattr(cli_plugins, "plugin_has_applied_migrations", lambda name: True)


@pytest.fixture
def unloaded(monkeypatch):
    monkeypatch.setattr(pluggy, "get_plugin", lambda name: None)


def is_enabled(registry: PluginRegistry) -> bool:
    db.session.refresh(registry)
    return registry.enabled


def post_as_admin(application, admin_user, view, name):
    with application.test_request_context(method="POST"):
        login_user(admin_user)
        return view().post(name)


def test_unknown_plugin_has_no_migrations(application):
    assert not utils.plugin_has_migrations("not_loaded_plugin")
    assert not utils.apply_plugin_migrations("not_loaded_plugin")


def test_enabling_applies_migrations(application, admin_user, dummy_registry, migrations):
    post_as_admin(application, admin_user, views.EnablePlugin, "dummy_plugin")

    assert migrations == ["dummy_plugin"]
    assert is_enabled(dummy_registry)


def test_failed_migrations_keep_plugin_disabled(
    application, admin_user, dummy_registry, failing_migrations
):
    post_as_admin(application, admin_user, views.EnablePlugin, "dummy_plugin")

    assert not is_enabled(dummy_registry)


def test_installing_applies_migrations(application, admin_user, dummy_registry, migrations):
    dummy_registry.enabled = True
    dummy_registry.save()

    post_as_admin(application, admin_user, views.InstallPlugin, "dummy_plugin")

    assert migrations == ["dummy_plugin"]


def test_installing_disabled_plugin_is_refused(application, admin_user, dummy_registry, migrations):
    post_as_admin(application, admin_user, views.InstallPlugin, "dummy_plugin")

    assert migrations == []


@pytest.mark.parametrize("enabled", [True, False])
def test_install_button_for_pending_migrations(
    application, admin_user, dummy_registry, monkeypatch, enabled
):
    monkeypatch.setattr(views, "plugin_has_pending_migrations", lambda name: True)
    dummy_registry.enabled = enabled
    dummy_registry.save()

    with application.test_request_context("/management/plugins"):
        login_user(admin_user)
        html = views.PluginsView().get()

    assert ("plugin-inst-dummy_plugin" in html) is enabled


def test_cli_enable_applies_migrations(cli_runner, dummy_registry, migrations):
    result = cli_runner.invoke(cli_plugins.enable_plugin, ["dummy_plugin"])

    assert result.exit_code == 0
    assert migrations == ["dummy_plugin"]
    assert is_enabled(dummy_registry)


def test_cli_enable_keeps_plugin_disabled_on_failure(
    cli_runner, dummy_registry, failing_migrations
):
    result = cli_runner.invoke(cli_plugins.enable_plugin, ["dummy_plugin"])

    assert result.exit_code != 0
    assert "stays disabled" in result.output
    assert not is_enabled(dummy_registry)


def test_uninstalling_reverts_migrations(
    application,
    admin_user,
    dummy_registry,
    applied_migrations,
    unloaded,
    reverted,
    removed_settings,
):
    post_as_admin(application, admin_user, views.UninstallPlugin, "dummy_plugin")

    assert reverted == ["dummy_plugin"]
    assert removed_settings == ["dummy_plugin"]


def test_uninstalling_loaded_plugin_keeps_its_tables(
    application, admin_user, dummy_registry, applied_migrations, reverted, removed_settings
):
    post_as_admin(application, admin_user, views.UninstallPlugin, "dummy_plugin")

    assert reverted == []
    assert removed_settings == []


def test_uninstalling_loaded_plugin_without_tables_removes_settings(
    application, admin_user, dummy_registry, reverted, removed_settings
):
    post_as_admin(application, admin_user, views.UninstallPlugin, "dummy_plugin")

    assert removed_settings == ["dummy_plugin"]


def test_failed_revert_keeps_settings(
    application,
    admin_user,
    dummy_registry,
    applied_migrations,
    unloaded,
    removed_settings,
    monkeypatch,
):
    def revert(name: str) -> bool:
        raise CommandError("boom")

    monkeypatch.setattr(views, "revert_plugin_migrations", revert)

    post_as_admin(application, admin_user, views.UninstallPlugin, "dummy_plugin")

    assert removed_settings == []


def test_uninstall_button_for_applied_migrations(
    application, admin_user, dummy_registry, applied_migrations
):
    with application.test_request_context("/management/plugins"):
        login_user(admin_user)
        html = views.PluginsView().get()

    assert "plugin-uninst-dummy_plugin" in html


@pytest.fixture
def stored_setting(dummy_registry):
    return Setting(key="ENABLED", value="true", group_key="dummy_plugin").save()


def test_cli_uninstall_reverts_migrations_and_settings(
    cli_runner, dummy_registry, stored_setting, applied_migrations, unloaded, reverted
):
    result = cli_runner.invoke(cli_plugins.uninstall, ["--force", "dummy_plugin"])

    assert result.exit_code == 0
    assert reverted == ["dummy_plugin"]
    assert not dummy_registry.has_stored_settings


def test_cli_uninstall_of_loaded_plugin_keeps_its_tables(
    cli_runner, dummy_registry, stored_setting, applied_migrations, reverted
):
    result = cli_runner.invoke(cli_plugins.uninstall, ["--force", "dummy_plugin"])

    assert "still in use" in result.output
    assert reverted == []
    assert dummy_registry.has_stored_settings


def test_cli_settings_only_uninstall_of_loaded_plugin(
    cli_runner, dummy_registry, stored_setting, applied_migrations, reverted
):
    result = cli_runner.invoke(cli_plugins.uninstall, ["--settings-only", "dummy_plugin"])

    assert "still in use" not in result.output
    assert reverted == []
    assert not dummy_registry.has_stored_settings


@pytest.mark.parametrize(("pending", "applied_badge"), [(False, True), (True, False)])
def test_applied_migrations_badge(
    application, admin_user, dummy_registry, applied_migrations, monkeypatch, pending, applied_badge
):
    monkeypatch.setattr(views, "plugin_has_pending_migrations", lambda name: pending)
    dummy_registry.enabled = True
    dummy_registry.save()

    with application.test_request_context("/management/plugins"):
        login_user(admin_user)
        html = views.PluginsView().get()

    assert (">migrations</span>" in html) is applied_badge
    assert ("requires migrations" in html) is pending


def _grant(group, key):
    group.permission_rows.append(GroupPermission(permission=key, level=PermissionLevel.ALLOW))
    group.save()


def _grants(prefix):
    return (
        db.session.execute(
            db.select(GroupPermission.permission).where(
                GroupPermission.permission.startswith(prefix)
            )
        )
        .scalars()
        .all()
    )


def test_uninstalling_removes_the_plugins_grants(
    application, admin_user, dummy_registry, reverted, removed_settings, default_groups
):
    _grant(default_groups[3], "dummy_plugin_do_things")

    post_as_admin(application, admin_user, views.UninstallPlugin, "dummy_plugin")

    assert _grants("dummy_plugin_") == []
    assert default_groups[3].permissions["editpost"]


def test_cli_uninstall_removes_the_plugins_grants(
    cli_runner, dummy_registry, reverted, removed_settings, default_groups
):
    _grant(default_groups[3], "dummy_plugin_do_things")

    result = cli_runner.invoke(cli_plugins.uninstall, ["--force", "dummy_plugin"])

    assert result.exit_code == 0
    assert _grants("dummy_plugin_") == []


def test_startup_adds_the_new_settings_of_an_installed_plugin(
    application, dummy_registry, dummy_settings
):
    db.session.add(Setting(key="OLD", value="5", group_key="dummy_plugin"))
    db.session.commit()
    Setting.invalidate_cache()

    upgrade_installed_plugin_settings(application)

    assert Setting.as_dict()["DUMMY_PLUGIN_OLD"] == 5
    assert Setting.as_dict()["DUMMY_PLUGIN_NEW"] == 2


def test_startup_does_not_install_a_plugin(application, dummy_registry, dummy_settings):
    upgrade_installed_plugin_settings(application)

    assert "DUMMY_PLUGIN_NEW" not in Setting.as_dict()


def test_startup_skips_plugin_settings_before_the_migrations(
    application, dummy_registry, dummy_settings
):
    db.session.execute(sa.text("ALTER TABLE settings RENAME TO old_settings"))
    try:
        upgrade_installed_plugin_settings(application)

        assert db.session.execute(sa.select(PluginRegistry)).scalars().all() == [dummy_registry]
    finally:
        db.session.execute(sa.text("ALTER TABLE old_settings RENAME TO settings"))
