Installation
============

-  `Basic Setup <#basic-setup>`_
-  `Configuration <#configuration>`_
-  `Deploying <#deploying>`_
-  `Deploying to PythonAnywhere <#deploying-to-pythonanywhere>`_



Basic Setup
-----------

We recommend installing FlaskBB in an isolated Python environment. This can be
achieved with `virtualenv`_. In our little guide we will use a wrapper around
virtualenv - the `virtualenvwrapper`_. In addition to virtualenv, we will also
use the package manager `pip`_ to install the dependencies for FlaskBB.


Virtualenv Setup
~~~~~~~~~~~~~~~~
**Linux:** The easiest way to install `virtualenv`_ and
`virtualenvwrapper`_ is, to use the package manager on your system (if you
are running Linux) to install them.

**Windows:** Take a look at the `flask`_ documentation (then skip ahead to dependencies).

For example, on archlinux you can install them with::

    $ sudo pacman -S python-virtualenvwrapper

or, on macOS, you can install them with::

    $ sudo pip install virtualenvwrapper

It's sufficient to just install the virtualenvwrapper because it depends on
virtualenv and the package manager will resolve all the dependencies for you.

After that, you can create your virtualenv with::

    $ mkvirtualenv -a /path/to/flaskbb -p $(which python) flaskbb

This will create a virtualenv named ``flaskbb`` using the python interpreter in
version 2 and it will set your project directory to ``/path/to/flaskbb``.
This comes handy when typing ``workon flaskbb`` as it will change your
current directory automatically to ``/path/to/flaskbb``.
To deactivate it you just have to type ``deactivate`` and if you want to work
on it again, just type ``workon flaskbb``.

It is also possible to use ``virtualenv`` without the ``virtualenvwrapper``.
For this you have to use the ``virtualenv`` command and pass the name
of the virtualenv as an argument. In our example, the name of
the virtualenv is ``.venv``.
::

    $ virtualenv .venv

and finally activate it
::

    $ source .venv/bin/activate

If you want to know more about those isolated python environments, checkout
the `virtualenv`_ and `virtualenvwrapper`_ docs.


Dependencies
~~~~~~~~~~~~

Now that you have set up your environment, you are ready to install the
dependencies.
::

    $ pip install -r requirements.txt

Alternatively, you can use the `make` command to install the dependencies.
::

    $ make dependencies


The development process requires a few extra dependencies which can be
installed with the provided ``requirements-dev.txt`` file.
::

    $ pip install -r requirements-dev.txt


Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

We have one optional dependency, redis (the python package is installed
automatically).
If you want to use it, make sure that a redis-server is running.
Redis will be used as the default result and caching backend for
celery (celery is a task queue which FlaskBB uses to send non blocking emails).
The feature for tracking the `online guests` and `online users` do also
require redis (although `online users` works without redis as well).
To install redis, just use your distributions package manager. For Arch Linux
this is `pacman` and for Debian/Ubuntu based systems this is `apt-get`.
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


Configuration
-------------

Production
~~~~~~~~~~

FlaskBB already sets some sane defaults, so you shouldn't have to change much.
To make this whole process a little bit easier for you, we have created
a little wizard which will ask you some questions and with the answers
you provide it will generate a configuration for you. You can of course
further adjust the generated configuration.

The setup wizard can be started with::

    flaskbb makeconfig


These are the only settings you have to make sure to setup accordingly if
you want to run FlaskBB in production:

- ``SERVER_NAME = "example.org"``
- ``PREFERRED_URL_SCHEME = "https"``
- ``SQLALCHEMY_DATABASE_URI = 'sqlite:///path/to/flaskbb.sqlite'``
- ``SECRET_KEY = "secret key"``
- ``WTF_CSRF_SECRET_KEY = "secret key"``

By default it will try to save the configuration file with the name flaskbb.cfg in FlaskBB’s root folder.

Finally to get going – fire up FlaskBB!
::

    flaskbb --config flaskbb.cfg run

    [+] Using config from: /path/to/flaskbb/flaskbb.cfg
    * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

Development
~~~~~~~~~~~

To get started with development you have to generate a development
configuration first. You can use the CLI for this,
as explained in `Configuration <#configuration>`_::

    flaskbb makeconfig -d

or::

    flaskbb makeconfig --development

Now you can either use ``make`` to run the development server::

    make run

or if you like to type a little bit more, the CLI::

    flaskbb --config flaskbb.cfg run

You can either pass an import string to the path to the (python) config file you’ve just created, or a default config object. (Most users will follow the example above, which uses the generated file).
This is how you do it by using an import string. Be sure that it is importable from within FlaskBB:

    flaskbb --config flaskbb.configs.default.DefaultConfig run

Redis
~~~~~

If you have decided to use redis as well, which we highly recommend, then
the following services and features can be enabled and configured to use redis.

Before you can start using redis, you have to enable and configure it.
This is quite easy just set ``REDIS_ENABLE`` to ``True`` and adjust the
``REDIS_URL`` if needed.
::

    REDIS_ENABLED = True
    REDIS_URL = "redis://localhost:6379"  # or with a password: "redis://:password@localhost:6379"
    REDIS_DATABASE = 0

The other services are already configured to use the ``REDIS_URL`` configuration
variable.

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
    RATELIMIT_STORAGE_URL = REDIS_URL


Mail Examples
~~~~~~~~~~~~~

Both methods are included in the example configs.

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
------------

**MySQL users:** Make sure that you create the database using the
``utf8`` charset::

    CREATE DATABASE flaskbb CHARACTER SET utf8;

Even though the ``utf8mb4`` charset is prefered today
(see `this <https://dba.stackexchange.com/a/152383>`_ SO answer), we have to
create our database using the ``utf8`` charset. A good explanation about this
issue can be found `here <https://stackoverflow.com/a/31474509>`_.

For a guided install, run::

    $ make install

or::

    flaskbb install

During the installation process you are asked about your username,
your email address and the password for your administrator user. Using the
``make install`` command is recommended as it checks that the dependencies
are also installed.


Upgrading
---------

If the database models changed after a release, you have to run the ``upgrade``
command::

    flaskbb db upgrade


Deploying
---------

This chapter will describe how to set up Supervisor + uWSGI + nginx for
FlaskBB as well as document how to use the built-in WSGI server (gunicorn)
that can be used in a productive environment.


Supervisor
~~~~~~~~~~

`Supervisor is a client/server system that allows its users to monitor and
control a number of processes on UNIX-like operating systems.`

To install `supervisor` on Debian, you need to fire up this command:
::

    $ sudo apt-get install supervisor

There are two ways to configure supervisor. The first one is, you just put
the configuration to the end in the ``/etc/supervisor/supervisord.conf`` file.

The second way would be to create a new file in the ``/etc/supervisor/conf.d/``
directory. For example, such a file could be named ``uwsgi.conf``.

After you have choosen the you way you like, simply put the snippet below in the
configuration file.

::

    [program:uwsgi]
    command=/usr/bin/uwsgi --emperor /etc/uwsgi/apps-enabled
    user=apps
    stopsignal=QUIT
    autostart=true
    autorestart=true
    redirect_stderr=true


uWSGI
~~~~~

`uWSGI is a web application solution with batteries included.`

To get started with uWSGI, you need to install it first.
You'll also need the python plugin to serve python apps.
This can be done with::

    $ sudo apt-get install uwsgi uwsgi-plugin-python

For the configuration, you need to create a file in the
``/etc/uwsgi/apps-available`` directory. In this example, I will call the
file ``flaskbb.ini``. After that, you can start with configuring it.
My config looks like this for `flaskbb.org` (see below). As you might have noticed, I'm
using a own user for my apps whose home directory is located at `/var/apps/`.
In this directory there are living all my Flask apps.

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


gunicorn
~~~~~~~~

`Gunicorn 'Green Unicorn' is a Python WSGI HTTP Server for UNIX.`

It's a pre-fork worker model ported from Ruby's Unicorn project.
The Gunicorn server is broadly compatible with various web frameworks,
simply implemented, light on server resources, and fairly speedy.

This is probably the easiest way to run a FlaskBB instance.
Just install gunicorn via pip inside your virtualenv::

    pip install gunicorn

and run FlaskBB using the  ``gunicorn`` command::

    gunicorn wsgi:flaskbb --log-file logs/gunicorn.log --pid gunicorn.pid -w 4


nginx
~~~~~

`nginx [engine x] is an HTTP and reverse proxy server,
as well as a mail proxy server, written by Igor Sysoev.`

The nginx config is pretty straightforward. Again, this is how I use it for
`FlaskBB`. Just copy the snippet below and paste it to, for example
``/etc/nginx/sites-available/flaskbb``.
The only thing left is, that you need to adjust the ``server_name`` to your
domain and the paths in ``access_log``, ``error_log``. Also, don't forget to
adjust the paths in the ``alias`` es, as well as the socket address in ``uwsgi_pass``.

::

    server {
        listen 80;
        server_name forums.flaskbb.org;

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

If you wish to use gunicorn instead of uwsgi just replace the ``location @flaskbb``
with this::

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


Like in the `uWSGI <#uwsgi>`_ chapter, don't forget to create a symlink to
``/etc/nginx/sites-enabled/``.


User Contributed Deployment Guides
----------------------------------

We do not maintain these deployment guides. They have been submitted by users
and we thought it is nice to include them in docs. If something is missing,
or doesn't work - please open a new pull request on GitHub.


Deploying to PythonAnywhere
~~~~~~~~~~~~~~~~~~~~~~~~~~~

`PythonAnywhere <https://www.pythonanywhere.com/>`_ is a
platform-as-a-service, which basically means they have a bunch of servers
pre-configured with Python, nginx and uWSGI.
You can run a low-traffic website with them for free,
so it's an easy way to get quickly FlaskBB running publicly.

Here's what to do:

* Sign up for a PythonAnywhere account at
  `https://www.pythonanywhere.com/ <https://www.pythonanywhere.com/>`_.
* On the "Consoles" tab, start a Bash console and install/configure
  FlaskBB like this

::

    git clone https://github.com/sh4nks/flaskbb.git
    cd flaskbb

Before continuing the installation it is advised to create a virtualenv as is
described in section `Virtualenv Setup <#virtualenv-setup>`_.

Finish the installation of FlaskBB by executing following commands::

    pip3.5 install --user -r requirements.txt
    pip3.5 install --user -e .
    flaskbb makeconfig
    flaskbb install

* Click the PythonAnywhere logo to go back to the dashboard,
  then go to the "Web" tab, and click the "Add a new web app" button.
* Just click "Next" on the first page.
* On the next page, click "Flask"
* On the next page, click "Python 3.5"
* On the next page, just accept the default and click next
* Wait while the website is created.
* Click on the "Source code" link, and in the input that appears,
  replace the `mysite` at the end with `flaskbb`
* Click on the "WSGI configuration file" filename,
  and wait for an editor to load.
* Change the line that sets `project_home` to replace `mysite` with `flaskbb`
  again.
* Change the line that says

::

    from flask_app import app as application

to say

::

    from flaskbb import create_app
    application = create_app("/path/to/your/configuration/file")

* Click the green "Save" button near the top right.
* Go back to the "Web" tab.
* Click the green "Reload..." button.
* Click the link to visit the site -- you'll have a new FlaskBB install!


.. _virtualenv: https://virtualenv.pypa.io/en/latest/installation.html
.. _virtualenvwrapper: http://virtualenvwrapper.readthedocs.org/en/latest/install.html#basic-installation
.. _pip: http://www.pip-installer.org/en/latest/installing.html
.. _flask: http://flask.pocoo.org/docs/0.12/installation/
