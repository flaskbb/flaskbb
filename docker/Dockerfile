# Release image: FlaskBB from a wheel, served by gunicorn.
# The build context is this directory:
#
#   docker build -f docker/Dockerfile -t flaskbb:release docker/
ARG PYTHON_VERSION=3.14
ARG UV_VERSION=0.12

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:${PYTHON_VERSION}-slim-trixie

COPY --from=uv /uv /uvx /usr/local/bin/

ARG FLASKBB_VERSION

COPY artifact/flaskbb-${FLASKBB_VERSION}-py3-none-any.whl /tmp/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    FLASKBB_SETTINGS=flaskbb.configs.docker.DockerConfig

# Flask creates its instance folder next to the venv, the app writes there
# and to its storage, everything else belongs to root.
RUN groupadd --gid 1000 flaskbb \
    && useradd --uid 1000 --gid 1000 --create-home flaskbb \
    && install -d -o flaskbb -g flaskbb \
        "$VIRTUAL_ENV/var/flaskbb-instance" \
        /var/lib/flaskbb /var/lib/flaskbb/avatars /var/lib/flaskbb/attachments

# the published -plugins images add the 'plugins' extra
ARG FLASKBB_EXTRAS=gunicorn,postgres,mysql
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv --allow-existing "$VIRTUAL_ENV" \
    && uv pip install "/tmp/flaskbb-${FLASKBB_VERSION}-py3-none-any.whl[${FLASKBB_EXTRAS}]"

WORKDIR /app

COPY wsgi.py /app/wsgi.py
COPY healthcheck.py /usr/local/lib/flaskbb-docker/healthcheck.py
COPY entrypoint.sh /usr/local/bin/flaskbb-entrypoint

USER flaskbb
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=40s --retries=10 \
    CMD ["python", "/usr/local/lib/flaskbb-docker/healthcheck.py", "8000"]

ENTRYPOINT ["flaskbb-entrypoint"]
# Worker count comes from WEB_CONCURRENCY, everything else from GUNICORN_CMD_ARGS.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "wsgi:flaskbb"]
