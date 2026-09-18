# FlaskBB in Docker

Two self-contained stacks:

| | development | release |
| --- | --- | --- |
| compose file | `compose.dev.yaml` | `compose.release.yaml` |
| FlaskBB | master, from this checkout | latest stable from PyPI |
| server | Flask dev server, reloader on | gunicorn |
| database | SQLite | PostgreSQL |
| extras | mailpit on <http://localhost:8025> | - |
| port | 5000 | 8000 |

Both run Valkey (Redis) and a Celery worker next to the forum, log to
stdout and store avatars and attachments in the `flaskbb-storage` volume.
The dev stack keeps its SQLite database there as well
(`/var/lib/flaskbb/flaskbb.sqlite`); set `DATABASE_URI` in `.env` to
develop against another database.

## Quickstart

```bash
cp docker/.env.example docker/.env
# set SECRET_KEY, CSRF_SECRET_KEY and ADMIN_PASSWORD
docker compose -f docker/compose.dev.yaml up --build
```

The forum is on <http://localhost:5000>, sent mails land in mailpit on
<http://localhost:8025>. The source tree is mounted into the container, so
edits on the host restart the dev server. The container runs as uid 1000;
if that is not your uid, build it once with `USER_UID` and `USER_GID` set
to yours, otherwise it cannot write to the mounted tree:

```bash
docker compose -f docker/compose.dev.yaml build \
    --build-arg USER_UID=$(id -u) --build-arg USER_GID=$(id -g)
```

For the stable release:

```bash
docker compose -f docker/compose.release.yaml up -d --build
```

`SECRET_KEY` and `POSTGRES_PASSWORD` have to be set for this one, the dev
stack falls back to insecure defaults. Put a reverse proxy in front of port
8000, terminate TLS there and set `SERVER_NAME`, `TRUSTED_HOSTS`,
`URL_SCHEME=https` and `PROXY_FIX=1` in `.env`.

## First start

The entrypoint runs `flaskbb bootstrap`, which waits for the database and
then either installs FlaskBB (empty database) or runs `flaskbb db upgrade`.
The administrator is created from `ADMIN_USERNAME`, `ADMIN_EMAIL` and
`ADMIN_PASSWORD`; without them the container stops and you install it
yourself, with the bootstrap reduced to waiting for the database:

```bash
docker compose -f docker/compose.dev.yaml run --rm -e FLASKBB_BOOTSTRAP=skip \
    flaskbb flaskbb install
```

`flaskbb bootstrap` is an ordinary FlaskBB command, so it works outside of
Docker as well, e.g. before starting a systemd service. `flaskbb bootstrap
--help` lists its options.

## Everyday commands

```bash
# any CLI command
docker compose -f docker/compose.dev.yaml exec flaskbb flaskbb --help
# a shell in the app context
docker compose -f docker/compose.dev.yaml exec flaskbb flaskbb shell
# the test suite (the dev image ships the dev dependency group)
docker compose -f docker/compose.dev.yaml exec flaskbb pytest
# start over
docker compose -f docker/compose.dev.yaml down -v
```

The image has no Node.js. Build the theme assets on the host instead, the
running container picks them up through the mounted source tree:

```bash
cd flaskbb/themes/aurora && npm install && npm run build
```

## Configuration

Both images contain `flaskbb.cfg` as `/etc/flaskbb/flaskbb.cfg`, read
through `FLASKBB_SETTINGS`. It is an ordinary FlaskBB config file that takes
its values from the environment and defaults to production values; the dev
stack sets the development ones (debug mode, SQLite, mailpit, verbose
logging) in `compose.dev.yaml` and mounts the file, so edits to it apply on
the next restart.

The release stack passes every variable of `.env` to its containers, so
most things are changed there - see `.env.example` for the complete list -
and applied with `up -d`. The dev stack only takes the database, secret,
host, search, log level and admin values from `.env`, the rest (mail,
https, proxy, plugins) would break it. Anything not covered can be set as a
`FLASKBB_<CONFIG_KEY>` environment variable, which FlaskBB applies on top of
the config file. To change the config file of the release image, mount your
own over it:

```yaml
    volumes:
      - ./my-flaskbb.cfg:/etc/flaskbb/flaskbb.cfg:ro
```

The release stack keeps at most 30 MB of logs per container (three rotated
10 MB files); read them with `docker compose logs`. On `docker compose
stop` or `down` it gives gunicorn and the Celery worker 60 seconds to finish
running requests and tasks.

Both images check their health by fetching a static file through the app
(`healthcheck.py`), with `SERVER_NAME` or the first `TRUSTED_HOSTS` entry
as the Host header. The Celery worker is checked with
`celery inspect ping` instead.

Only the PostgreSQL and MySQL drivers are installed on top of FlaskBB,
through its `postgres` and `mysql` extras (`psycopg`, `pymysql`). Point
`DATABASE_URI` at something else and the driver has to be added to the
image.

The release image installs whatever is the current release on PyPI. Pin it
with `FLASKBB_VERSION=2.2.0` in `.env` to control when an upgrade happens -
the entrypoint migrates the database on the next start.

Every release tag also publishes a prebuilt release image for linux/amd64
and linux/arm64, tagged `<version>`, `<major>.<minor>` and `latest`
(pre-releases only get `<version>`):

```bash
docker pull ghcr.io/flaskbb/flaskbb:latest
```

The image runs without the compose stack as well, it only needs a database,
a redis and the variables from `.env.example`:

```bash
docker run -d -p 8000:8000 -v flaskbb-storage:/var/lib/flaskbb \
    -e DATABASE_URI=postgresql+psycopg://flaskbb:secret@db.example.org/flaskbb \
    -e REDIS_URL=redis://redis.example.org:6379 \
    -e SECRET_KEY=... -e ADMIN_USERNAME=admin \
    -e ADMIN_EMAIL=admin@example.org -e ADMIN_PASSWORD=... \
    ghcr.io/flaskbb/flaskbb:latest
```

## Plugins

Plugins of the release stack are declared in `.env`, so every image built
from it has them, including the ones built for a new FlaskBB version:

```
# PyPI packages that are installed into the image
FLASKBB_PLUGINS="flaskbb-plugin-portal flaskbb-plugin-conversations"
# the names they register as, see 'flaskbb plugins list'
FLASKBB_ENABLE_PLUGINS=portal,conversations
```

```bash
docker compose -f docker/compose.release.yaml up -d --build
```

On start the entrypoint enables every listed plugin that isn't enabled yet
and runs `flaskbb plugins install` for it, which adds its settings and
applies its migrations. Plugins that are already enabled are not touched
again: FlaskBB adds their new settings when it starts and the entrypoint's
`flaskbb db upgrade` applies their new migrations.

To upgrade, change `FLASKBB_VERSION` and run `up -d --build` again. The
plugins are resolved together with FlaskBB, so an unpinned plugin gets its
newest release that supports the new version, and a pinned plugin that
doesn't support it fails the build instead of the running forum. Docker
reuses the install layer as long as `FLASKBB_VERSION` and `FLASKBB_PLUGINS`
don't change, so pin the plugins (`flaskbb-plugin-portal==3.0.0`) and bump
the pin to get a newer plugin release, or build with `--no-cache`.

To remove a plugin, take it out of `FLASKBB_ENABLE_PLUGINS` first, otherwise
the next start enables it again. Then uninstall it while it is still
enabled, which drops its settings and reverts its migrations, disable it,
remove the package from `FLASKBB_PLUGINS` and rebuild:

```bash
docker compose -f docker/compose.release.yaml exec flaskbb flaskbb plugins uninstall portal
docker compose -f docker/compose.release.yaml exec flaskbb flaskbb plugins disable portal
```

The prebuilt images on ghcr.io come without plugins.

## Known issues

The release stack will work as soon as FlaskBB 3.0.0 is released.

## Layout

```
Dockerfile.dev        master from the source tree, context is the repo root
Dockerfile.release    latest stable from PyPI, context is this directory
compose.dev.yaml      dev stack
compose.release.yaml  release stack
entrypoint.sh         runs 'flaskbb bootstrap', then the container command
healthcheck.py        health check of the web containers
wsgi.py               gunicorn entry point, optional ProxyFix
flaskbb.cfg           FlaskBB config of both images
.dockerignore         keeps everything but the copied files (.env!) out of
                      the release build context
.env.example          every supported environment variable
```
