"""migrate plugin store

Revision ID: 1784020734
Revises: 1783713047
Create Date: 2026-07-14 11:18:54.816846

"""

import json
import pickle
import warnings

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1784020734"
down_revision = "1783713047"
branch_labels = ()
depends_on = None


def upgrade():
    conn = op.get_bind()

    plugin_store = sa.table(
        "plugin_store",
        sa.column("plugin_id", sa.Integer),
        sa.column("key", sa.String),
        sa.column("value", sa.LargeBinary),
    )
    plugin_registry = sa.table(
        "plugin_registry",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
    )
    settings_table = sa.table(
        "settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
        sa.column("group_key", sa.String),
    )

    collisions, orphans = _check_for_collisions(conn, plugin_store, plugin_registry, settings_table)

    if collisions:
        details = "\n".join(f"  - {c}" for c in collisions)
        raise RuntimeError(
            f"Found {len(collisions)} setting key collision(s) - resolve "
            f"these manually before running this migration:\n{details}"
        )

    for orphan in orphans:
        warnings.warn(f"plugin_store: {orphan}", stacklevel=2)

    plugins = {
        row.id: row.name
        for row in conn.execute(sa.select(plugin_registry.c.id, plugin_registry.c.name))
    }

    rows = conn.execute(
        sa.select(plugin_store.c.plugin_id, plugin_store.c.key, plugin_store.c.value)
    ).fetchall()

    for plugin_id, key, raw_value in rows:
        plugin_name = plugins.get(plugin_id)
        if plugin_name is None:
            # orphaned row, already reported above - skip rather than
            # fail the migration
            continue

        # settings.key is stored lower-case (see lowercase_setting_keys) -
        # plugin_store had no such convention, so normalize on the way in
        lower_key = key.lower()

        try:
            python_value = pickle.loads(raw_value)
        except Exception as e:
            raise RuntimeError(
                f"Could not unpickle plugin setting '{key}' for plugin '{plugin_name}': {e}"
            ) from e

        conn.execute(
            settings_table.insert().values(
                key=lower_key,
                value=json.dumps(python_value),
                group_key=plugin_name,
            )
        )

    op.drop_table("plugin_store")


def downgrade():
    # Recreating plugin_store from settings rows isn't attempted here -
    # once a plugin's settings are moved into the shared settings table,
    # there's no reliable way to tell which rows originated from
    # plugin_store versus core/other plugins without keeping a separate
    # marker. If you need to support downgrading past this revision,
    # back up plugin_store's contents before running upgrade().
    raise NotImplementedError(
        "Downgrading past this revision is not supported - restore "
        "plugin_store from a backup taken before this migration ran."
    )


def _check_for_collisions(
    conn: sa.Connection,
    plugin_store: sa.TableClause,
    plugin_registry: sa.TableClause,
    settings_table: sa.TableClause,
):
    """Read-only pre-check, run before any writes happen. Returns
    (collisions, orphans):

    - collisions: fatal - a plugin_store key that collides
      case-insensitively with an existing settings key, or with another
      plugin's key in plugin_store. Raises if any are found.
    - orphans: non-fatal - plugin_store rows whose plugin_id has no
      matching plugin_registry entry. These get skipped by the
      migration rather than migrated, so they're reported as warnings
      rather than failing the migration outright.
    """
    plugins = {
        row.id: row.name
        for row in conn.execute(sa.select(plugin_registry.c.id, plugin_registry.c.name))
    }
    existing_settings_keys = {
        key.lower() for key in conn.execute(sa.select(settings_table.c.key)).scalars()
    }

    rows = conn.execute(sa.select(plugin_store.c.plugin_id, plugin_store.c.key)).fetchall()

    collisions: list[str] = []
    orphans: list[str] = []
    seen_in_plugin_store: dict[str, str] = {}  # lower_key -> plugin_name

    for plugin_id, key in rows:
        plugin_name = plugins.get(plugin_id)
        lower_key = key.lower()

        if plugin_name is None:
            orphans.append(
                f"plugin_store key '{key}' references plugin_id={plugin_id}, "
                f"which has no matching plugin_registry entry - will be "
                f"skipped, not migrated."
            )
            continue

        if lower_key in existing_settings_keys:
            collisions.append(
                f"key '{lower_key}' (plugin_store, plugin '{plugin_name}') "
                f"already exists in the settings table."
            )

        if lower_key in seen_in_plugin_store:
            other_plugin = seen_in_plugin_store[lower_key]
            if other_plugin != plugin_name:
                collisions.append(
                    f"key '{lower_key}' is used by both plugin "
                    f"'{other_plugin}' and plugin '{plugin_name}' in "
                    f"plugin_store."
                )
        else:
            seen_in_plugin_store[lower_key] = plugin_name

    return collisions, orphans
