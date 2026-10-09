.. _docker-deployment:

Docker Deployment
=================

FlaskBB provides a production Docker Compose stack with Gunicorn, PostgreSQL,
Valkey, and a Celery worker. The stack is intended to run behind a reverse
proxy that terminates TLS.

Prerequisites
-------------

Install Docker Engine with the Docker Compose plugin, then obtain a FlaskBB
release checkout containing the ``docker`` directory. Run all commands below
from the repository root.

Initial deployment
------------------

Copy the example environment file::

    $ cp docker/.env.example docker/.env

Set at least these values in ``docker/.env``:

``SECRET_KEY``
    A long random value used to sign sessions and tokens. Generate one with
    ``python -c "import secrets; print(secrets.token_hex(32))"``.

``POSTGRES_PASSWORD``
    A strong password for the PostgreSQL user.

``ADMIN_USERNAME``, ``ADMIN_EMAIL``, and ``ADMIN_PASSWORD``
    Credentials for the administrator created during the first start. They
    are not reapplied after FlaskBB has been installed.

For an internet-facing forum, also configure:

``SERVER_NAME``
    The public hostname, such as ``forum.example.org``.

``TRUSTED_HOSTS``
    A comma-separated list of accepted hostnames. Usually this contains the
    same hostname as ``SERVER_NAME``.

``URL_SCHEME``
    Set this to ``https`` when the reverse proxy provides HTTPS.

``PROXY_FIX``
    Set this to ``1`` when the reverse proxy sends the standard forwarded
    headers.

Start the stack::

    $ docker compose -f docker/docker-compose.yaml up -d

The forum is published on port ``8000`` by default. Set ``FLASKBB_PORT`` in
``docker/.env`` to change the host port. Do not expose this port directly to
the internet; route traffic through an HTTPS reverse proxy.

On the first start, the web container waits for PostgreSQL, creates the
database schema, and creates the administrator. On later starts it applies
database migrations before Gunicorn starts. The Celery worker starts only
after the web service becomes healthy.

Check the deployment with::

    $ docker compose -f docker/docker-compose.yaml ps
    $ docker compose -f docker/docker-compose.yaml logs -f flaskbb celery

Persistent data
---------------

The Compose stack stores data in three named volumes:

``postgres-data``
    The PostgreSQL database.

``redis-data``
    Valkey data used by caching and background jobs.

``flaskbb-storage``
    Uploaded avatars and attachments.

Stopping or recreating containers does not remove these volumes. Never run
``docker compose down -v`` during normal maintenance because ``-v`` deletes
the persistent data.

Reverse proxy
-------------

The reverse proxy must preserve the original host and scheme. For nginx, the
proxy location can be configured as follows::

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_pass http://127.0.0.1:8000;
    }

Configure TLS certificates and HTTP-to-HTTPS redirects in the reverse proxy.
With ``URL_SCHEME=https``, the container configuration also marks session and
remember-me cookies as secure.

Configuration
-------------

The image loads ``flaskbb.configs.docker.DockerConfig`` through
``FLASKBB_SETTINGS``. The Compose stack passes the values from ``docker/.env``
to the FlaskBB containers. Common options include:

``FLASKBB_IMAGE``
    The image tag to deploy. Pin a release such as
    ``ghcr.io/flaskbb/flaskbb:3.0.0`` for reproducible upgrades. The
    ``-plugins`` tags, e.g. ``3.0.0-plugins``, contain all official plugins.

``WEB_CONCURRENCY``
    The number of Gunicorn worker processes. The default is ``4``.

``MAIL_SERVER``, ``MAIL_PORT``, ``MAIL_USERNAME``, and ``MAIL_PASSWORD``
    SMTP connection settings. The sender is controlled by
    ``MAIL_SENDER_NAME`` and ``MAIL_SENDER_ADDRESS``.

``SEARCH_BACKEND``
    The search backend. The production Compose stack defaults to
    ``postgresql``.

``LOG_LEVEL``
    FlaskBB's application log level. Container logs are written to standard
    output and rotated by Docker Compose.

Any FlaskBB configuration key not listed in ``docker/.env.example`` can be
set with a ``FLASKBB_`` prefix. For example, ``SESSION_COOKIE_SAMESITE`` can
be overridden with ``FLASKBB_SESSION_COOKIE_SAMESITE``. Restart the web and
worker services after changing configuration::

    $ docker compose -f docker/docker-compose.yaml up -d

Administration
--------------

Run FlaskBB CLI commands in the web container::

    $ docker compose -f docker/docker-compose.yaml exec flaskbb flaskbb --help
    $ docker compose -f docker/docker-compose.yaml exec flaskbb flaskbb plugins list

The admin panel and the ``flaskbb plugins`` commands are the source of truth
for whether a plugin is enabled. Container restarts do not change that state.

Installing plugins
------------------

The ``-plugins`` release images (e.g. ``ghcr.io/flaskbb/flaskbb:latest-plugins``)
contain all official plugins. Set ``FLASKBB_IMAGE`` to one of them and enable
the plugins you want.

Other plugins must be installed in both the web and Celery images. Add their
PyPI package names to ``docker/.env``::

    FLASKBB_PLUGINS="flaskbb-plugin-example another-flaskbb-plugin"

Build and start the plugin image with the Compose override::

    $ docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml up -d --build

Find the plugin registration names with ``flaskbb plugins list``. Enable and
install each plugin in separate commands so the second process loads the newly
enabled plugin::

    $ docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml exec flaskbb flaskbb plugins enable portal
    $ docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml exec flaskbb flaskbb plugins install portal

Restart the web and worker services after changing plugin state::

    $ docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml restart flaskbb celery

The same operations are available in the admin panel. Follow its restart
notices before configuring or installing a newly enabled plugin.

To remove a plugin, uninstall it while it is enabled, then disable it::

    $ docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml exec flaskbb flaskbb plugins uninstall portal
    $ docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml exec flaskbb flaskbb plugins disable portal

Remove its package from ``FLASKBB_PLUGINS``, rebuild the plugin image, and
restart the stack.

Backups and upgrades
--------------------

Back up PostgreSQL and ``flaskbb-storage`` before every upgrade. A logical
PostgreSQL backup can be created with::

    $ docker compose -f docker/docker-compose.yaml exec -T postgres sh -c \
        'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > flaskbb.sql

Back up the ``flaskbb-storage`` named volume with the volume tooling provided
by the Docker host or hosting platform. Keep database and storage backups from
the same maintenance window.

To upgrade a pinned deployment, change ``FLASKBB_IMAGE`` in ``docker/.env``,
then pull and recreate the services::

    $ docker compose -f docker/docker-compose.yaml pull
    $ docker compose -f docker/docker-compose.yaml up -d

The entrypoint applies FlaskBB migrations and migrations for enabled plugins
before starting the application. Watch the logs and service health during the
upgrade::

    $ docker compose -f docker/docker-compose.yaml logs -f flaskbb celery

When using ``docker/docker-compose.plugin.yaml``, rebuild the plugin image
against the updated FlaskBB image before recreating the services::

    $ docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml build --pull flaskbb
    $ docker compose -f docker/docker-compose.yaml -f docker/docker-compose.plugin.yaml up -d

Troubleshooting
---------------

If a service is unhealthy or restarting, inspect its status and recent logs::

    $ docker compose -f docker/docker-compose.yaml ps
    $ docker compose -f docker/docker-compose.yaml logs --tail=200 flaskbb celery postgres redis

The web health check requests a static file through FlaskBB. A wrong
``SERVER_NAME`` or ``TRUSTED_HOSTS`` value can therefore make the container
unhealthy even when Gunicorn is listening. Database connection and migration
errors appear in the ``flaskbb`` service logs.
