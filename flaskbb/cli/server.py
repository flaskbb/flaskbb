# -*- coding: utf-8 -*-
"""
    flaskbb.cli.plugins
    ~~~~~~~~~~~~~~~~~~~

    This module contains all plugin commands.

    :copyright: (c) 2016 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import os
import signal

from flask.cli import pass_script_info
import click

from flaskbb._compat import iteritems
from flaskbb.cli.main import flaskbb
from flaskbb.cli.utils import FlaskBBCLIError


def get_gunicorn_pid(pid, instance_path):
    if os.path.exists(pid):  # pidfile provided
        with open(pid) as pidfile:
            pid = int(pidfile.readline().strip())
    elif pid:  # pid provided
        pid = int(pid)
        try:
            os.kill(pid, 0)
        except OSError:
            pid = None
    else:  # nothing provided, lets try to get the pid from flaskbb.pid
        pid = None
        pidfile = os.path.join(instance_path, "flaskbb.pid")
        if os.path.exists(pidfile):
            with open(pidfile) as f:
                pid = int(f.readline().strip())

    return pid


@flaskbb.group()
def server():
    """Manages the start and stop process of the gunicorn WSGI server. \n
    Gunicorn is made for UNIX-like operating systems and thus Windows is not
    supported.\n

    For proper monitoring of the Gunicorn/FlaskBB process it is advised
    to use a real process monitoring system like 'supervisord' or
    'systemd'.
    """
    pass


@server.command()
@click.option("--host", "-h", default="127.0.0.1", show_default=True,
              help="The interface to bind to.")
@click.option("--port", "-p", default="8000", type=int, show_default=True,
              help="The port to bind to.")
@click.option("--workers", "-w", default=4, show_default=True,
              help="The number of worker processes for handling requests.")
@click.option("--daemon", "-d", default=False, is_flag=True, show_default=True,
              help="Starts gunicorn as daemon.")
@click.option("--pid", "-p", default=None, help="Path to a PID file. "
              "If the instance directory exists, it will store the Pidfile "
              "there.")
@pass_script_info
def start(info, host, port, workers, daemon, pid):
    """Starts a preconfigured gunicorn instance."""
    try:
        from gunicorn.app.base import Application
    except ImportError:
        raise FlaskBBCLIError("Cannot import gunicorn. "
                              "Make sure it is installed.", fg="red")

    class FlaskBBApplication(Application):
        def __init__(self, app, options=None, args=None):
            self.options = options or {}
            self.application = app
            super(FlaskBBApplication, self).__init__()

        def load_config(self):
            config = dict([
                (key, value) for key, value in iteritems(self.options)
                if key in self.cfg.settings and value is not None
            ])
            for key, value in iteritems(config):
                print(key, value)
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    flaskbb_app = info.load_app()
    default_pid = None
    if os.path.exists(flaskbb_app.instance_path):
        default_pid = os.path.join(flaskbb_app.instance_path, "flaskbb.pid")

    options = {
        "bind": "{}:{}".format(host, port),
        "workers": workers,
        "daemon": daemon,
        "pidfile": pid or default_pid
    }
    FlaskBBApplication(flaskbb_app, options).run()


@server.command()
@click.option("--pid", "-p", default="", help="The PID or the path to "
              "the PID file. By default it tries to get the PID file from the "
              "instance folder.")
@click.option("--force", "-f", default=False, is_flag=True, show_default=True,
              help="Kills gunicorn ungratefully.")
@pass_script_info
def stop(info, pid, force):
    """Stops the gunicorn process."""
    app = info.load_app()
    pid = get_gunicorn_pid(pid, app.instance_path)

    if pid is None:
        raise FlaskBBCLIError("Neither a valid PID File nor a PID that exist "
                              "was provided.", fg="red")

    try:
        if force:
            os.kill(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        click.secho("Process with PID '{}' not found. Are you sure that "
                    "Gunicorn/FlaskBB is running?".format(pid), fg="yellow")


@server.command()
@click.option("--pid", "-p", default="", help="The PID or the path to "
              "the PID file. By default it tries to get the PID file from the "
              "instance folder.")
@pass_script_info
def status(info, pid):
    """Shows the status of gunicorn."""
    app = info.load_app()
    pid = get_gunicorn_pid(pid, app.instance_path)

    if pid is None:
        click.secho("Gunicorn/FlaskBB is not running.", fg="red")
    else:
        click.secho("Gunicorn/FlaskBB is running.", fg="green")
