# FlaskBB development Docker stack

This stack runs FlaskBB from the source tree with the Flask development server,
SQLite, Valkey, a Celery worker and Mailpit. The SQLite database, avatars and
attachments use the `flaskbb-storage` volume.

## Quickstart

From the repository root:

```bash
docker compose -f docker/docker-compose.dev.yaml up --build
```

The forum is on <http://localhost:5000> and Mailpit is on
<http://localhost:8025>. The default administrator is `admin` with password
`test1234`.

The source tree is mounted into the container, so edits on the host restart
the development server. The container runs as uid 1000 by default. If your
uid or gid differs, build with matching values before starting the stack:

```bash
docker compose -f docker/docker-compose.dev.yaml build \
    --build-arg USER_UID=$(id -u) --build-arg USER_GID=$(id -g)
docker compose -f docker/docker-compose.dev.yaml up
```

## Everyday commands

```bash
# run a FlaskBB CLI command
docker compose -f docker/docker-compose.dev.yaml exec flaskbb flaskbb --help
# open a shell in the app context
docker compose -f docker/docker-compose.dev.yaml exec flaskbb flaskbb shell
# run the test suite
docker compose -f docker/docker-compose.dev.yaml exec flaskbb pytest
# remove containers and development data
docker compose -f docker/docker-compose.dev.yaml down -v
```

## Configuration

The image contains `flaskbb.cfg` as `/etc/flaskbb/flaskbb.cfg`, read through
`FLASKBB_SETTINGS`. The Compose file mounts `docker/flaskbb.cfg`, so edits to
that file apply on the next restart.

The Compose file uses SQLite, debug mode, Mailpit and verbose logging by
default. It reads database, secret, host, search, log level and administrator
values from `docker/.env` when present. Copy `docker/.env.example` to
`docker/.env` to customize them. Other variables in that file are intended
for the release stack and are not passed to the development containers.

The web container checks its health by fetching a static file through the
app. The Celery worker uses `celery inspect ping`.
