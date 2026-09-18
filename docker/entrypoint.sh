#!/bin/sh
set -e

# FLASKBB_BOOTSTRAP=skip only waits for the database, e.g. for the worker
if [ "${FLASKBB_BOOTSTRAP:-auto}" = "skip" ]; then
    flaskbb bootstrap --wait-only
else
    flaskbb bootstrap
fi

exec "$@"
