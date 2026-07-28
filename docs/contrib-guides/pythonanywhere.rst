.. _deploying-to-pythonanywhere:

Deploying to PythonAnywhere
============================

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

Before continuing the installation it is advised to set up ``uv`` as is
described in section :ref:`installing-uv`.

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
