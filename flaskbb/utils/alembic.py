from __future__ import annotations

import logging
import os
import typing as t

import sqlalchemy as sa
from alembic.runtime.migration import MigrationContext, MigrationStep
from alembic.script import Script
from alembic.util.exc import CommandError
from flask_alembic import Alembic as FlaskAlembic
from flask_alembic.extension import t_rev

from flaskbb.utils.proxies import current_app

logger = logging.getLogger(__name__)

type MigrationFn = t.Callable[
    [str | list[str] | tuple[str, ...], MigrationContext], list[MigrationStep]
]


class Alembic(FlaskAlembic):
    @t.override
    def run_migrations(
        self,
        fn: MigrationFn,
        skip_missing: bool = False,
        **kwargs: t.Any,
    ) -> None:
        """Runs the migrations with foreign key enforcement suspended on SQLite.

        SQLite can't alter most columns in place, so batch operations copy a
        table, drop the original and rename the copy. Dropping a table that
        other rows still reference fails while foreign keys are enforced.

        Revisions the database holds that no installed package provides fail
        the run, unless ``skip_missing`` migrates around them.
        """
        fn = self._around_unknown_revisions(fn, skip_missing)

        connections = [
            context.connection
            for context in self.migration_contexts.values()
            if context.connection is not None and context.connection.dialect.name == "sqlite"
        ]
        for connection in connections:
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")

        try:
            super().run_migrations(fn, **kwargs)
        finally:
            for connection in connections:
                # the connection goes back to the pool, where the connect
                # listener that normally turns this on will not run again
                connection.exec_driver_sql("PRAGMA foreign_keys=ON")

        # databases from before 3.0 never enforced foreign keys on SQLite
        for connection in connections:
            for table, rowid, parent, _ in connection.exec_driver_sql("PRAGMA foreign_key_check"):
                logger.warning(
                    "Foreign key violation: %s row %s references a missing row in %s",
                    table,
                    rowid,
                    parent,
                )

    @t.override
    def upgrade(self, target: int | str | Script = "heads", skip_missing: bool = False) -> None:
        """Runs migrations to upgrade the database.

        The migrations of disabled plugins are loaded so the revisions they
        already applied still resolve, but ``heads`` leaves them out. They run
        once the plugin is enabled. ``skip_missing`` upgrades around the
        revisions of plugins that are no longer installed.
        """
        destination: str | list[str]
        if target == "heads":
            disabled_locations = tuple(
                os.path.join(location, "")
                for location in current_app.config["MIGRATIONS_DISABLED_VERSION_LOCATIONS"]
            )
            destination = [
                script.revision
                for script in self.script_directory.get_revisions("heads")
                if not script.path.startswith(disabled_locations)
            ]
        else:
            destination = self._simplify_rev(target, handle_int=True)
            if len(destination) == 1:
                # like in Flask-Alembic, a relative target (+1) must be a single value
                destination = destination[0]

        def do_upgrade(
            revision: str | list[str] | tuple[str, ...], context: MigrationContext
        ) -> list[MigrationStep]:
            return self.script_directory._upgrade_revs(destination, revision)  # type: ignore[arg-type,return-value]  # pyright: ignore[reportPrivateUsage, reportArgumentType, reportReturnType]

        self.run_migrations(do_upgrade, skip_missing=skip_missing)

    @t.override
    def revision(
        self,
        message: str,
        empty: bool = False,
        branch: str = "default",
        parent: t_rev = "head",
        splice: bool = False,
        depend: t_rev | None = None,
        label: str | list[str] | None = None,
        path: str | None = None,
    ) -> list[Script | None]:
        """Creates a new revision. It may only build on FlaskBB's and its own
        branch's revisions, a plugin never on the revisions of another plugin.
        """
        # Flask-Alembic points these at the revision's own branch
        references = [
            rev
            for rev in self._simplify_rev(parent) + self._simplify_rev(depend or [])
            if rev not in ("base", "head")
        ]
        foreign = self._plugin_branches(references) - {branch}
        if foreign:
            raise CommandError(
                f"The revision of '{branch}' would depend on the migrations of "
                f"{', '.join(sorted(foreign))}. Plugin migrations may only depend on "
                "FlaskBB's and their own. If the plugins go hand in hand, add the "
                "dependency to the revision by hand and require the other plugin "
                "in pyproject.toml."
            )

        return super().revision(message, empty, branch, parent, splice, depend, label, path)

    @t.override
    def merge(
        self,
        revisions: t_rev = "heads",
        message: str | None = None,
        label: str | list[str] | None = None,
    ) -> Script | None:
        """Creates a merge revision. It may only merge the revisions of one
        plugin, optionally with FlaskBB's.
        """
        plugins = self._plugin_branches(self._simplify_rev(revisions))
        if len(plugins) > 1:
            raise CommandError(
                f"A merge revision would join the migrations of {', '.join(sorted(plugins))}. "
                "Merge the heads of one plugin at a time, e.g. 'flaskbb db merge <plugin>@head'."
            )

        return super().merge(revisions, message, label)

    def _plugin_branches(self, revisions: list[str]) -> set[str]:
        return {
            label
            for script in self.script_directory.get_revisions(tuple(revisions))
            for label in script.branch_labels
            if label != "default"
        }

    def _around_unknown_revisions(self, fn: MigrationFn, skip_missing: bool) -> MigrationFn:
        """Alembic can't locate a revision the database holds once the package
        of a plugin with migrations is removed from the env without
        uninstalling the plugin first. ``skip_missing`` hides those revisions
        from the migrations, so their rows stay and the plugin picks up where
        it left off once it is reinstalled.
        """
        current = [
            revision
            for context in self.migration_contexts.values()
            for revision in context.get_current_heads()
        ]
        known = {script.revision for script in self.script_directory.walk_revisions()}
        unknown = sorted(set(current) - known)
        if not unknown:
            return fn

        # without a row of its own, FlaskBB's position would be guessed from the
        # plugins' dependencies and its applied migrations would run again
        skippable = any(
            "default" in script.branch_labels
            for script in self.script_directory.get_revisions(
                tuple(revision for revision in current if revision in known)
            )
        )
        if not skip_missing:
            raise self._unknown_revisions_error(unknown, skippable)
        if not skippable:
            raise CommandError(
                f"Can't skip {', '.join(unknown)}. No other revision in the database "
                "records FlaskBB's own migrations, so they may be FlaskBB's. Install "
                "the version of FlaskBB that applied them."
            )

        logger.warning(
            "Skipping the unknown revisions %s, they stay in the database.", ", ".join(unknown)
        )

        def skip_unknown(
            revision: str | list[str] | tuple[str, ...], context: MigrationContext
        ) -> list[MigrationStep]:
            return fn(tuple(rev for rev in revision if rev not in unknown), context)

        return skip_unknown

    def _unknown_revisions_error(self, unknown: list[str], skippable: bool) -> CommandError:
        # flaskbb.extensions imports this module
        from flaskbb.extensions import db, pluggy
        from flaskbb.plugins.models import PluginRegistry

        registered = db.session.execute(sa.select(PluginRegistry.name)).scalars()
        missing = sorted(set(registered) - set(pluggy.list_plugin_metadata()))

        message = (
            "The database holds migrations that no installed package provides: "
            f"{', '.join(unknown)}."
        )
        if missing:
            message += (
                f" These plugins are registered but not installed: {', '.join(missing)}."
                " Reinstall them and try again. To remove a plugin for good, run"
                " 'flaskbb plugins uninstall <plugin>' before removing its package."
            )
        elif skippable:
            message += " A plugin that is no longer installed applied them."
        else:
            message += (
                " A plugin that is no longer installed or a newer version of FlaskBB applied them."
            )
        if skippable:
            message += " To upgrade without them, run 'flaskbb db upgrade --skip-missing'."
        return CommandError(message)
