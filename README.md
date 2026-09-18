<p align="center">
  <a href="https://flaskbb.com">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/flaskbb/flaskbb/master/docs/_static/logo-full-dark.svg">
      <img src="https://raw.githubusercontent.com/flaskbb/flaskbb/master/docs/_static/logo-full-light.svg" alt="FlaskBB" height="72">
    </picture>
  </a>
</p>

<p align="center">
  <strong>A classic forum software in Python using Flask.</strong>
</p>

<p align="center">
  <a href="https://github.com/flaskbb/flaskbb/actions/workflows/tests.yml"><img src="https://github.com/flaskbb/flaskbb/actions/workflows/tests.yml/badge.svg" alt="Build Status"></a>
  <a href="https://codecov.io/gh/flaskbb/flaskbb"><img src="https://codecov.io/gh/flaskbb/flaskbb/branch/master/graph/badge.svg" alt="Coverage"></a>
  <a href="https://pypi.org/project/FlaskBB/"><img src="https://img.shields.io/pypi/v/flaskbb.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/FlaskBB/"><img src="https://img.shields.io/pypi/pyversions/flaskbb.svg" alt="Python Versions"></a>
  <a href="https://github.com/flaskbb/flaskbb/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-BSD--3--Clause-blue.svg" alt="License"></a>
  <a href="https://matrix.to/#/#flaskbb:matrix.org"><img src="https://img.shields.io/badge/[matrix]-%23flaskbb%3Amatrix.org-blue" alt="Matrix"></a>
</p>

<p align="center">
  <a href="https://flaskbb.com">Website</a> -
  <a href="https://flaskbb.readthedocs.io">Documentation</a> -
  <a href="https://github.com/flaskbb/flaskbb/blob/master/CHANGES.md">Changelog</a> -
  <a href="https://github.com/flaskbb/flaskbb/issues">Issues</a>
</p>

---

FlaskBB is a forum software written in Python on top of the
[Flask](https://flask.palletsprojects.com) web framework. It aims to be a
classic message board with a modern look, and to stay small enough that it is
easy to host, theme and extend.

<p align="center">
  <img src="https://raw.githubusercontent.com/flaskbb/flaskbb/master/docs/_static/index.webp" alt="FlaskBB forum index with the Aurora theme" width="800">
</p>


## Features

- **Forums, topics and posts** with categories, unread tracking and a topic tracker
- **Markdown** posts with syntax highlighting, emoji and an editor toolbar
- **Attachments and avatars** that users can upload and admins can manage
- **Full-text search** for PostgreSQL and SQLite, extendable through plugins
- **Group based permissions** and per-forum moderators
- **Admin panel** for users, groups, forums, reports, plugins and settings
- **Plugin system** built on [pluggy](https://pluggy.readthedocs.io), the library behind pytest's plugins
- **Themeable**, ships with the Aurora theme in a light and a dark variant
- **Command line interface** for installing, serving and managing users, groups and plugins
- **i18n** with translations for more than a dozen languages


## Quick start

### Running with Docker

Release images are published to the GitHub Container Registry for
linux/amd64 and linux/arm64:

```bash
docker pull ghcr.io/flaskbb/flaskbb:latest
```

The repository contains a complete release stack with PostgreSQL, Valkey,
a Celery worker and gunicorn:

```bash
git clone https://github.com/flaskbb/flaskbb.git
cd flaskbb
cp docker/.env.example docker/.env
```

Set `SECRET_KEY`, `POSTGRES_PASSWORD` and the `ADMIN_*` variables in
`docker/.env`, then start it:

```bash
docker compose -f docker/compose.release.yaml up -d --build
```

The forum is served on [localhost:8000](http://localhost:8000). See
[docker/README.md](docker/README.md) for the development stack, configuration
and reverse proxy setup.

### Running from source

FlaskBB requires Python 3.12 or newer and uses [uv](https://docs.astral.sh/uv/)
to manage its environment.

```bash
git clone https://github.com/flaskbb/flaskbb.git
cd flaskbb
make devconfig
make install
make run
```

`make install` asks for the administrator's username, email and password.
Afterwards visit [localhost:5000](http://localhost:5000).

For a production setup with gunicorn, a reverse proxy, Redis and Celery,
follow the [deployment guide](https://flaskbb.readthedocs.io/en/latest/production/deployment.html).


## Plugins

Plugins are regular Python packages that are discovered through entry points.
Newly installed plugins are disabled until they are enabled in the admin panel
or with the CLI:

```bash
uv pip install flaskbb-plugin-like
uv run flaskbb plugins install like
uv run flaskbb plugins enable like
```

| Plugin | Description |
| --- | --- |
| [portal](https://github.com/flaskbb/flaskbb-plugin-portal) | A simple portal page for the forum. Installed by default. |
| [conversations](https://github.com/flaskbb/flaskbb-plugin-conversations) | Private messages between users. Installed by default. |
| [like](https://github.com/flaskbb/flaskbb-plugin-like) | Let users like posts and see who liked them. |
| [vote](https://github.com/flaskbb/flaskbb-plugin-vote) | Single or multiple choice polls on topics and posts. |
| [ranks](https://github.com/flaskbb/flaskbb-plugin-ranks) | User ranks. |
| [inviteonly](https://github.com/flaskbb/flaskbb-plugin-inviteonly) | Invite-only registration, even while registration is closed. |

To write your own, start with the
[plugin development guide](https://flaskbb.readthedocs.io/en/latest/development/plugin/index.html)
or generate a skeleton with
[cookiecutter-flaskbb-plugin](https://github.com/sh4nks/cookiecutter-flaskbb-plugin).
Themes can be scaffolded the same way with
[cookiecutter-flaskbb-theme](https://github.com/sh4nks/cookiecutter-flaskbb-theme).


## Community

- Ask questions and discuss development in the [#flaskbb:matrix.org](https://matrix.to/#/#flaskbb:matrix.org) chat
- Report bugs and request features in the [issue tracker](https://github.com/flaskbb/flaskbb/issues)


## Contributing

Contributions of any size are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md)
before opening a pull request. The short version:

```bash
uv sync
make test
make format
```

Translations are managed on [Transifex](https://www.transifex.com). See the
[localization guide](https://flaskbb.readthedocs.io/en/latest/development/localization.html)
for adding a new language.


## License

FlaskBB is licensed under the [BSD 3-Clause License](LICENSE). Code adapted
from other projects is listed in [NOTICE](NOTICE), and the people behind
FlaskBB are listed in [AUTHORS](AUTHORS).
