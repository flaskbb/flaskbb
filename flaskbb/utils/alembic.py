from __future__ import annotations

import logging
import os
import typing as t

from alembic.config import Config
from alembic.runtime.migration import MigrationContext, MigrationStep
from alembic.script import Script
from flask import current_app
from flask_alembic import Alembic as FlaskAlembic

logger = logging.getLogger(__name__)


class Alembic(FlaskAlembic):
    @t.override
    def run_migrations(
        self,
        fn: t.Callable[[str | list[str] | tuple[str, ...], MigrationContext], list[MigrationStep]],
        **kwargs: t.Any,
    ) -> None:
        """Runs the migrations with foreign key enforcement suspended on SQLite.

        SQLite can't alter most columns in place, so batch operations copy a
        table, drop the original and rename the copy. Dropping a table that
        other rows still reference fails while foreign keys are enforced.
        """
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
    def upgrade(self, target: int | str | Script = "heads") -> None:
        """Runs migrations to upgrade the database.

        The migrations of disabled plugins are loaded so the revisions they
        already applied still resolve, but ``heads`` leaves them out. They run
        once the plugin is enabled.
        """
        if target != "heads":
            super().upgrade(target)
            return

        disabled_locations = tuple(
            os.path.join(location, "")
            for location in t.cast(
                list[str], current_app.config["ALEMBIC"]["disabled_version_locations"]
            )
        )
        heads = [
            script.revision
            for script in self.script_directory.get_revisions("heads")
            if not script.path.startswith(disabled_locations)
        ]

        def do_upgrade(
            revision: str | list[str] | tuple[str, ...], context: MigrationContext
        ) -> list[MigrationStep]:
            return self.script_directory._upgrade_revs(heads, revision)  # pyright: ignore[reportPrivateUsage, reportArgumentType, reportReturnType]

        self.run_migrations(do_upgrade)

    @property
    @t.override
    def config(self) -> Config:
        """Get the Alembic :class:`~alembic.config.Config` for the
        current app.
        """
        cache = self._get_cache()

        if cache.config is not None:
            return cache.config

        cache.config = c = Config()
        script_location = t.cast(str, current_app.config["ALEMBIC"]["script_location"])

        if not os.path.isabs(script_location) and ":" not in script_location:
            script_location = os.path.join(current_app.root_path, script_location)

        version_locations: list[str] = [script_location]

        for item in current_app.config["ALEMBIC"]["version_locations"]:
            version_location = t.cast(str, item if isinstance(item, str) else item[1])

            if not os.path.isabs(version_location) and ":" not in version_location:
                version_location = os.path.join(current_app.root_path, version_location)

            version_locations.append(version_location)

        c.set_main_option("script_location", script_location)
        c.set_main_option("path_separator", current_app.config["ALEMBIC"]["path_separator"])
        # path_separator is always set above, so this is never None
        path_sep = t.cast(str, c._get_file_separator_char("path_separator"))
        c.set_main_option(
            "version_locations",
            path_sep.join(version_locations),
        )

        for key, value in current_app.config["ALEMBIC"].items():
            if key in (
                "script_location",
                "version_locations",
                "disabled_version_locations",
                "path_separator",
            ):
                continue

            if isinstance(value, dict):
                for inner_key, inner_value in value.items():
                    c.set_section_option(key, inner_key, inner_value)
            else:
                c.set_main_option(key, value)

        if len(self.metadatas) > 1:
            # Add the names used by the multidb template.
            c.set_main_option("databases", ", ".join(self.metadatas))

        return cache.config
