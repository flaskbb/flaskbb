import zipfile
import urllib
import os
import shutil
import json

import pytest
from click.testing import CliRunner
from flaskbb.cli import main as cli_main
from flaskbb import plugins
from importlib import import_module


def test_new_plugin(tmpdir, application, monkeypatch):
    runner = CliRunner()
    # download the cookiecutter file to use locally
    # (bypasses prompt about re-cloning)
    zipfilename = str(tmpdir.join('cookiecutter.zip'))
    urllib.urlretrieve('https://github.com/sh4nks/cookiecutter-flaskbb-plugin/archive/master.zip', zipfilename)  # noqa
    with zipfile.ZipFile(zipfilename) as zf:
        zf.extractall(str(tmpdir))
    cookiecutterpath = tmpdir.join('cookiecutter-flaskbb-plugin-master')

    tmp_plugin_folder = str(tmpdir.join('plugin_folder'))
    os.mkdir(tmp_plugin_folder)
    monkeypatch.setattr(cli_main, 'create_app', lambda s: application)
    monkeypatch.setattr(application.extensions['plugin_manager'],
                        'plugin_folder', tmp_plugin_folder)
    stdin = '\n'.join([
        'Test Name',
        'someone@nowhere.com',
        'Testing Plugin',
        '',
        'TestingPlugin',
        'Straightforward Test Plugin',
        'www.example.com',
        '1.0.0'
    ])

    result = runner.invoke(
        cli_main.flaskbb,
        ['plugins', 'new', 'testplugin', '--template', str(cookiecutterpath)],
        input=stdin
    )

    assert result.exit_code == 0
    plugin_dir = os.path.join(
        application.extensions['plugin_manager'].plugin_folder,
        'testing_plugin'
    )
    assert os.path.exists(plugin_dir)
    assert os.path.isdir(plugin_dir)
    # add the temporary folder to the plugins path
    # so import flaskbb.plugins.test_plugin works as expected
    monkeypatch.setattr(
        plugins, '__path__', plugins.__path__ + [tmp_plugin_folder]
    )
    assert import_module('flaskbb.plugins.testing_plugin').__plugin__ == 'TestingPlugin'  # noqa


def test_migrate_plugin(tmpdir, monkeypatch, application):
    pluginmanager = application.extensions['plugin_manager']
    orig_plugin_folder = pluginmanager.plugin_folder
    tmp_plugin_folder = str(tmpdir.join('plugin_folder'))
    os.mkdir(tmp_plugin_folder)
    shutil.copytree(
        os.path.join(orig_plugin_folder, '_migration_environment'),
        os.path.join(tmp_plugin_folder, '_migration_environment')
    )
    os.mkdir(os.path.join(tmp_plugin_folder, 'testplugin'))

    pyfile = os.path.join(tmp_plugin_folder, 'testplugin', '__init__.py')
    with open(pyfile, 'w') as pyfile:
        pyfile.write('\r\n'.join([
            "from flaskbb.plugins import FlaskBBPlugin",
            "from flaskbb.extensions import db",
            "class TestPlugin(FlaskBBPlugin):",
            "    settings_key='testplugin'",
            "    def somequery(self):",
            "        TestModel.query.all()",
            "class TestModel(db.Model):",
            "    __tablename__='testtable'",
            "    testkey=db.Column(db.Integer,primary_key=True)",
            "",
            "__plugin__='TestPlugin'",
        ]))

    jsoninfo = {
        "identifier": "testplugin",
        "name": "TestPlugin",
        "author": "sh4nks",
        "website": "http://flaskbb.org",
        "license": "BSD",
        "description": "A Test Plugin for FlaskBB",
        "version": "0.1"
    }
    jsonfile = os.path.join(tmp_plugin_folder, 'testplugin', 'info.json')
    with open(jsonfile, 'w') as jsonfile:
        json.dump(jsoninfo, jsonfile)

    monkeypatch.setattr(cli_main, 'create_app', lambda s: application)

    monkeypatch.setattr(pluginmanager, 'plugin_folder', tmp_plugin_folder)
    # add the temporary folder to the plugins path
    # so import flaskbb.plugins.test_plugin works as expected
    monkeypatch.setattr(
        plugins, '__path__', plugins.__path__ + [tmp_plugin_folder]
    )
    pluginmanager._plugins = None
    pluginmanager._all_plugins = None
    pluginmanager._available_plugins = dict()
    pluginmanager._found_plugins = dict()
    pluginmanager.setup_plugins()
    assert 'testplugin' in pluginmanager.plugins
    versionsdir = os.path.join(
        tmp_plugin_folder, 'testplugin', 'migration_versions'
    )
    assert not os.path.exists(versionsdir)
    testplugin = pluginmanager.plugins['testplugin']

    with application.app_context():
        testplugin.migrate()
        assert os.path.exists(versionsdir)

        dirlist = os.listdir(versionsdir)
        assert dirlist

        dirlist = [os.path.join(versionsdir, d)
                   for d in dirlist if d.endswith('.py')]

        for d in dirlist:
            with open(d, 'r') as f:
                output = '\n'.join([l for l in f])

        assert 'testtable' in output
        exception_msg = 'Should not be able to run migrations twice'
        with pytest.raises(Exception, message=exception_msg):
            testplugin.migrate()

        exception_msg = "Operations should fail as model not yet registered"
        with pytest.raises(Exception, message=exception_msg):
            testplugin.somequery()

        testplugin.upgrade_database()
