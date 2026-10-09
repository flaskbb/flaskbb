# FlaskBB + Docker

For the development stack, see [DEVELOPMENT.md](DEVELOPMENT.md).

This README explains the release/deployment configuration of FlaskBB  with gunicorn, PostgreSQL,
Valkey and a Celery worker. Avatars, attachments and database files use named volumes.

## Quickstart

Start FlaskBBs docker setup with:

```bash
cp docker/.env.example docker/.env
# set SECRET_KEY, POSTGRES_PASSWORD and the ADMIN_* values in docker/.env
docker compose -f docker/docker-compose.yaml up -d
```

The application server runs on port 8000. Configure a reverse proxy to terminate
TLS before exposing it publicly.
Set `SERVER_NAME`, `TRUSTED_HOSTS`, `URL_SCHEME=https` and `PROXY_FIX=1` in `.env`.


## First start

The entrypoint runs `flaskbb bootstrap`. On an empty database, it installs
FlaskBB and creates an administrator from `ADMIN_USERNAME`, `ADMIN_EMAIL` and
`ADMIN_PASSWORD`. On later starts, it applies database migrations. Without
administrator credentials, install interactively with:

```bash
docker compose -f docker/docker-compose.yaml run --rm -e FLASKBB_BOOTSTRAP=skip \
    flaskbb flaskbb install
```

## Configuration

The image loads `flaskbb.configs.docker.DockerConfig` through
`FLASKBB_SETTINGS`. This configuration takes values from the environment and
provides production defaults.

Our docker-compose config passes every variable of `.env` to its containers, so
most settings can be changed there. See `.env.example` for the full list, then
apply the changes by running `up -d`. Anything not covered can be set as a
`FLASKBB_<CONFIG_KEY>` environment variable. To use a custom configuration
file, mount it and set `FLASKBB_SETTINGS` for both the `flaskbb` and `celery`
services:

```yaml
    environment:
      FLASKBB_SETTINGS: /etc/flaskbb/custom.cfg
    volumes:
      - ./my-flaskbb.cfg:/etc/flaskbb/custom.cfg:ro
```

This setup keeps at most 30 MB of logs per container (three rotated
10 MB files); read them with `docker compose logs`. On `docker compose
stop` or `down` it gives gunicorn and the Celery worker 60 seconds to finish
running requests and tasks.

The web container checks its health by fetching a static file through the app
(`healthcheck.py`), using `SERVER_NAME` or the first `TRUSTED_HOSTS` entry as
the Host header. The Celery worker uses `celery inspect ping`.

This image comes with `postgres`, `mysql` and `sqlite` drivers and all official
plugins (`FlaskBB[plugins]`) pre-installed. The plugins stay disabled until you
enable them.
While all 3 are supported I have only tested `postgres` and `sqlite` myself!

The Compose stack uses `ghcr.io/flaskbb/flaskbb:latest` by default. Set
`FLASKBB_IMAGE` in `.env` to pin an exact version or a release series. Upgrade
the standard stack with `docker compose down`, `docker compose pull` and
`docker compose up -d`. The entrypoint migrates the database on startup. Do not
use `down -v`, which removes the data volumes.

Every release tag also publishes a prebuilt release image for linux/amd64
and linux/arm64, tagged `<version>`, `<major>.<minor>` and `latest`
(pre-releases only get `<version>`):

```bash
docker pull ghcr.io/flaskbb/flaskbb:latest
```

The image runs without the docker-compose as well, it only needs a database,
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

The release image already contains all official plugins. `Dockerfile.plugin`
adds additional plugin packages on top of it. List the PyPI packages in `.env`:

```
FLASKBB_PLUGINS="flaskbb-plugin-example another-flaskbb-plugin"
```

Build and start the derived image by applying the plugin Compose file after the
standard one:

```bash
docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml up -d --build
```

The build keeps the FlaskBB version from `FLASKBB_IMAGE` and installs only the
additional plugin layer. Enable and install the plugins through the admin panel
or the CLI, then restart the web and worker processes so they load them:

```bash
docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml exec flaskbb flaskbb plugins enable portal
docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml exec flaskbb flaskbb plugins install portal
docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml restart flaskbb celery
```

To remove a plugin, uninstall it while it is still enabled, which drops its
settings and reverts its migrations. Then disable it, remove the package from
`FLASKBB_PLUGINS` and rebuild:

```bash
docker compose -f docker/docker-compose.yaml exec flaskbb flaskbb plugins uninstall portal
docker compose -f docker/docker-compose.yaml exec flaskbb flaskbb plugins disable portal
```

The prebuilt images on ghcr.io come with all official plugins.


### Updating a plugin image

Back up PostgreSQL and the `flaskbb-storage` volume before upgrading. If
`FLASKBB_IMAGE` is pinned, update its tag in `.env`; no edit is needed when it
uses `latest`. Pull the base image and rebuild the plugin layer:

```bash
docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml build --pull flaskbb
```

Optionally pull updates for PostgreSQL and Valkey, then recreate the services:

```bash
docker compose -f docker/docker-compose.yaml pull postgres redis
docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml up -d
```

FlaskBB applies database and enabled-plugin migrations before starting.
Running `down` first is not required. Never use `down -v` during an update
because it removes the data volumes.
