Installation
============

-  `Basic Setup <#basic-setup>`_
-  `Configuration <#configuration>`_
-  `Deplyoing <#deploying>`_



Basic Setup
===========

Virtualenv Setup
~~~~~~~~~~~~~~~~

Before you can start, you need to create a `virtualenv`.

::

    $ mkvirtualenv flaskbb


Required Dependencies
~~~~~~~~~~~~~~~~~~~~~

Now you can install the required dependencies.

::

     $ pip install -r requirements.txt


Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~~

We have two optional dependencies, redis (the python package is installed automatically).
If you want to use redis, be sure that a redis-server is running.


On Archlinux
------------

::

    # Install redis
    $ sudo pacman -S redis

    # Check if redis is already running.
    $ systemctl status redis

    # If not, start it.
    $ sudo systemctl start redis

    # Optional: Start redis everytime you boot your machine
    $ sudo systemctl enable redis



Configuration
=============


Google Mail Example
~~~~~~~~~~~~~~~~~~~


Local SMTP Server Example
~~~~~~~~~~~~~~~~~~~~~~~~~



Deploying
=========


Supervisor
~~~~~~~~~~


uWSGI
~~~~~


nginx
~~~~~
