.. _production-deployment:

Production & Deployment
=========================

-  `Setup & Prerequisites`_
-  `Installation`_
-  `Servers`_
-  `systemd Unit Files`_


Setup & Prerequisites
-----------------------

FlaskBB requires Python 3.12 or newer and uses `uv`_ to manage its Python
environment and dependencies. Install ``uv`` itself as described in
:ref:`installing-uv` in the development setup guide.

Once ``uv`` is installed, sync the project's dependencies *without* the
``dev`` dependency group (pytest, ruff, sphinx, ...) - you don't need any of
that in production::

    $ uv sync --no-dev

This creates a ``.venv`` folder and installs everything pinned in
``uv.lock`` except the ``dev`` group. Prefix commands with ``uv run`` (e.g.
``uv run flaskbb run``) to execute them inside that environment.

If you plan to serve FlaskBB with gunicorn (see `uWSGI / Gunicorn`_ below),
sync with that extra enabled too::

    $ uv sync --no-dev --extra gunicorn


Configuration
~~~~~~~~~~~~~~~

FlaskBB already sets some sane defaults, so you shouldn't have to change
much. To make this whole process a little bit easier for you, we have
created a little wizard which will ask you some questions and, based on the
answers that you provide, generate a configuration for you. You can of
course further adjust the generated configuration.

The setup wizard can be started with::

    uv run flaskbb makeconfig

To be able to run FlaskBB in production, the only settings that you need to
modify are the following:

- ``SERVER_NAME = "example.org"``
- ``PREFERRED_URL_SCHEME = "https"``
- ``SQLALCHEMY_DATABASE_URI = 'sqlite:///path/to/flaskbb.sqlite'``
- ``SECRET_KEY = "secret key"``
- ``WTF_CSRF_SECRET_KEY = "secret key"``
- ``TRUSTED_HOSTS = ["example.org"]`` -- rejects requests with a forged
  ``Host`` header instead of reflecting it into emailed links
  (password reset, account activation)

By default it will try to save the configuration file with the name
``flaskbb.cfg`` in FlaskBB's root folder.


Mail
~~~~~~

Both of these are included in the example configs.

**Google Mail**
::

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = "your_username@gmail.com"
    MAIL_PASSWORD = "your_password"
    MAIL_DEFAULT_SENDER = ("Your Name", "your_username@gmail.com")

**Local SMTP Server**
::

    MAIL_SERVER = "localhost"
    MAIL_PORT = 25
    MAIL_USE_SSL = False
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    MAIL_DEFAULT_SENDER = "noreply@example.org"


Installation
-------------

Database Setup
~~~~~~~~~~~~~~~~

Point ``SQLALCHEMY_DATABASE_URI`` in your generated config at the database
you want to use before continuing.

**MySQL users:** Make sure that you create the database using the ``utf8``
charset::

    CREATE DATABASE flaskbb CHARACTER SET utf8;

Even though the ``utf8mb4`` charset is prefered today
(see `this <https://dba.stackexchange.com/a/152383>`_ SO answer), we have to
create our database using the ``utf8`` charset. A good explanation about
this issue can be found `here <https://stackoverflow.com/a/31474509>`_.

For a guided install, which creates the database tables, default groups,
and your admin user, run::

    $ make install

or::

    uv run flaskbb install

During the installation process, you will be asked to provide a username,
email address and password for your administrator user.

If the database models change after a release, run the ``upgrade`` command
to bring an existing database up to date::

    uv run flaskbb db upgrade

Finally, to get going - fire up FlaskBB!
::

    uv run flaskbb --config flaskbb.cfg run

    [+] Using config from: /path/to/flaskbb/flaskbb.cfg
    * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

That's Flask's own development server though - see `Servers`_ below for
running FlaskBB behind a real WSGI server, and `systemd Unit Files`_ for
keeping it (and Celery) running as a proper service.


Servers
--------

.. _redis:

Redis (optional)
~~~~~~~~~~~~~~~~~~

We have one optional dependency, redis (the python package is installed
automatically). If you want to use it, make sure that a redis-server is
running. Redis will be used as the default result and caching backend for
celery (celery is a task queue which FlaskBB uses to send non blocking
emails). The feature for tracking the `online guests` and `online users` do
also require redis (although `online users` works without redis as well).
To install redis, just use your distributions package manager. For Arch
Linux this is `pacman` and for Debian/Ubuntu based systems this is
`apt-get`.
::

    # Installing redis using 'pacman':
    $ sudo pacman -S redis
    # Installing redis using 'apt-get':
    $ sudo apt-get install redis-server

    # Check if redis is already running.
    $ systemctl status redis

    # If not, start it.
    $ sudo systemctl start redis

    # Optional: Lets start redis everytime you boot your machine
    $ sudo systemctl enable redis

Once redis is running, enable and configure it in your FlaskBB config -
just set ``REDIS_ENABLED`` to ``True`` and adjust the ``REDIS_URL`` if
needed::

    REDIS_ENABLED = True
    REDIS_URL = "redis://localhost:6379"  # or with a password: "redis://:password@localhost:6379"
    REDIS_DATABASE = 0

The other services are already configured to use the ``REDIS_URL``
configuration variable.

**Celery**
::

    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

**Caching**
::

    CACHE_TYPE = "redis"
    CACHE_REDIS_URL = REDIS_URL

**Rate Limiting**
::

    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = REDIS_URL


uWSGI / Gunicorn
~~~~~~~~~~~~~~~~~~

FlaskBB needs a WSGI server in front of it - pick one of the two below.
Either can be supervised directly by `systemd Unit Files`_, or by
Supervisor if you'd rather not use systemd.

**Gunicorn**

`Gunicorn 'Green Unicorn' is a Python WSGI HTTP Server for UNIX.` It's a
pre-fork worker model ported from Ruby's Unicorn project. The Gunicorn
server is broadly compatible with various web frameworks, simply
implemented, light on server resources, and fairly speedy.

This is probably the easiest way to run a FlaskBB instance. Sync with the
``gunicorn`` extra enabled (see `Setup & Prerequisites`_ above), then run
FlaskBB using the ``gunicorn`` command::

    uv run gunicorn wsgi:flaskbb --log-file logs/gunicorn.log --pid gunicorn.pid -w 4

**uWSGI**

`uWSGI is a web application solution with batteries included.`

To get started with uWSGI, you need to install it first. You'll also need
the python plugin to serve python apps. This can be done with::

    $ sudo apt-get install uwsgi uwsgi-plugin-python

For the configuration, you need to create a file in the
``/etc/uwsgi/apps-available`` directory. In this example, I will call the
file ``flaskbb.ini``. After that, you can start with configuring it. My
config looks like this for `flaskbb.com` (see below). As you might have
noticed, I'm using a own user for my apps whose home directory is located
at `/var/apps/`. All my flask apps live in this directory.

::

    [uwsgi]
    base = /var/apps/flaskbb
    home = /var/apps/.virtualenvs/flaskbb/
    pythonpath = %(base)
    socket = 127.0.0.1:30002
    module = wsgi
    callable = flaskbb
    uid = apps
    gid = apps
    logto = /var/apps/flaskbb/logs/uwsgi.log
    plugins = python


===============  ==========================  ===============
**base**         /path/to/flaskbb            The folder where your flaskbb application lives
**home**         /path/to/virtualenv/folder  The virtualenv folder for your flaskbb application
**pythonpath**   /path/to/flaskbb            The same as base
**socket**       socket                      This can be either a ip or the path to a socket (don't forget to change that in your nginx config)
**module**       wsgi.py                     This is the file located in the root directory from flaskbb (where manage.py lives).
**callable**     flaskbb                     The callable is application you have created in the ``wsgi.py`` file
**uid**          your_user                   The user who should be used. **NEVER** use root!
**gid**          your_group                  The group who should be used.
**logto**        /path/to/log/file           The path to your uwsgi logfile
**plugins**      python                      We need the python plugin
===============  ==========================  ===============

Don't forget to create a symlink to ``/etc/uwsgi/apps-enabled``.

::

    ln -s /etc/uwsgi/apps-available/flaskbb /etc/uwsgi/apps-enabled/flaskbb

**Supervisor** (alternative to systemd)

`Supervisor is a client/server system that allows its users to monitor and
control a number of processes on UNIX-like operating systems.` To install
it on Debian::

    $ sudo apt-get install supervisor

There are two ways to configure supervisor. The first one is, you just put
the configuration to the end in the ``/etc/supervisor/supervisord.conf``
file. The second way would be to create a new file in the
``/etc/supervisor/conf.d/`` directory, for example one named ``uwsgi.conf``.
Either way, put the snippet below in the configuration file::

    [program:uwsgi]
    command=/usr/bin/uwsgi --emperor /etc/uwsgi/apps-enabled
    user=apps
    stopsignal=QUIT
    autostart=true
    autorestart=true
    redirect_stderr=true


nginx (reverse proxy)
~~~~~~~~~~~~~~~~~~~~~~~

`nginx [engine x] is an HTTP and reverse proxy server, as well as a mail
proxy server, written by Igor Sysoev.`

The nginx config is pretty straightforward. Again, this is how I use it for
`FlaskBB`. Just copy the snippet below and paste it to, for example
``/etc/nginx/sites-available/flaskbb``. The only thing left is, that you
need to adjust the ``server_name`` to your domain and the paths in
``access_log``, ``error_log``. Also, don't forget to adjust the paths in
the ``alias`` es, as well as the socket address in ``uwsgi_pass``.

::

    server {
        listen 80;
        server_name forums.flaskbb.com;

        access_log /var/log/nginx/access.forums.flaskbb.log;
        error_log /var/log/nginx/error.forums.flaskbb.log;

        location / {
            try_files $uri @flaskbb;
        }

        # Static files
        location /static {
           alias /var/apps/flaskbb/flaskbb/static/;
        }

        location ~ ^/_themes/([^/]+)/(.*)$ {
            alias /var/apps/flaskbb/flaskbb/themes/$1/static/$2;
        }

        # robots.txt
        location /robots.txt {
            alias /var/apps/flaskbb/flaskbb/static/robots.txt;
        }

        location @flaskbb {
            uwsgi_pass 127.0.0.1:30002;
            include uwsgi_params;
        }
    }

If you wish to use gunicorn instead of uwsgi just replace the
``location @flaskbb`` with this::

    location @flaskbb {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        #proxy_set_header SCRIPT_NAME /forums;  # This line will make flaskbb available on /forums;
        proxy_redirect off;
        proxy_buffering off;

        proxy_pass http://127.0.0.1:8000;
    }

Don't forget to adjust the ``proxy_pass`` address to your socket address.
Like in the uWSGI section above, don't forget to create a symlink to
``/etc/nginx/sites-enabled/``.


Celery Worker
~~~~~~~~~~~~~~~

Celery is the task queue FlaskBB uses to send non-blocking emails (and any
other background jobs plugins register). Start a worker with::

    uv run flaskbb celery worker

This is just a preconfigured wrapper around the ``celery`` command -
additional arguments are passed straight through, e.g. ``flaskbb celery
worker --loglevel=info`` or ``flaskbb celery beat``. It requires
``CELERY_BROKER_URL`` to be configured - see `Redis (optional)`_ above, or
point it at another broker.


systemd Unit Files
--------------------

If you don't want to use Supervisor, `systemd <https://systemd.io/>`_
(available by default on most modern Linux distributions) can supervise
FlaskBB's gunicorn process and Celery worker for you just as well.


Gunicorn
~~~~~~~~~~

Create a unit file at ``/etc/systemd/system/flaskbb.service``:

::

    [Unit]
    Description=FlaskBB Gunicorn Daemon
    After=network.target

    [Service]
    User=apps
    Group=apps
    WorkingDirectory=/var/apps/flaskbb
    Environment="PATH=/var/apps/flaskbb/.venv/bin"
    ExecStart=/var/apps/flaskbb/.venv/bin/gunicorn wsgi:flaskbb \
        --workers 4 \
        --bind 127.0.0.1:8000 \
        --log-file /var/apps/flaskbb/logs/gunicorn.log
    Restart=on-failure
    RestartSec=5

    [Install]
    WantedBy=multi-user.target

Adjust ``User``, ``Group``, ``WorkingDirectory`` and the ``.venv`` path to
match your setup - they follow the same ``/var/apps/flaskbb`` layout used in
the uWSGI example above. ``--bind 127.0.0.1:8000`` matches the address the
nginx config above proxies to.

Then enable and start the service::

    $ sudo systemctl daemon-reload
    $ sudo systemctl enable --now flaskbb

You can check on it and tail its logs with::

    $ sudo systemctl status flaskbb
    $ journalctl -u flaskbb -f


Celery Worker
~~~~~~~~~~~~~~~

Create a unit file at ``/etc/systemd/system/flaskbb-celery.service``:

::

    [Unit]
    Description=FlaskBB Celery Worker
    After=network.target

    [Service]
    User=apps
    Group=apps
    WorkingDirectory=/var/apps/flaskbb
    Environment="PATH=/var/apps/flaskbb/.venv/bin"
    ExecStart=/var/apps/flaskbb/.venv/bin/flaskbb celery worker --loglevel=info
    Restart=on-failure
    RestartSec=5

    [Install]
    WantedBy=multi-user.target

Adjust ``User``, ``Group``, ``WorkingDirectory`` and the ``.venv`` path the
same way as the gunicorn unit above. Then enable and start it::

    $ sudo systemctl daemon-reload
    $ sudo systemctl enable --now flaskbb-celery

You can check on it and tail its logs with::

    $ sudo systemctl status flaskbb-celery
    $ journalctl -u flaskbb-celery -f


User Contributed Guides
--------------------------

Platform-specific deployment walkthroughs (e.g. PythonAnywhere) submitted by
users and not maintained by the FlaskBB team:

.. toctree::
   :maxdepth: 2

   ../contrib-guides/index


.. _uv: https://docs.astral.sh/uv/
