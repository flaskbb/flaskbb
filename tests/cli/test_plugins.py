
import click
import zipfile,urllib,os
from click.testing import CliRunner
from flaskbb.cli import main as cli_main

def test_new_plugin(tmpdir,application,monkeypatch):
    runner=CliRunner()
    zipfilename=str(tmpdir.join('cookiecutter.zip'))
    monkeypatch.setattr(cli_main,'create_app',lambda s: application)
    urllib.urlretrieve('https://github.com/sh4nks/cookiecutter-flaskbb-plugin/archive/master.zip',zipfilename)
    with zipfile.ZipFile(zipfilename) as zf:
        zf.extractall(str(tmpdir))
    cookiecutterpath=tmpdir.join('cookiecutter-flaskbb-plugin-master')
    input='\n'.join([
    'Test Name',
    'someone@nowhere.com',
    'Testing Plugin',
    '',
    '',
    'Straightforward Test Plugin',
    'www.example.com',
    '1.0.0'])

    result=runner.invoke(cli_main.flaskbb,['plugins','new','testplugin','--template',str(cookiecutterpath)],input=input)
    assert result.exit_code == 0
    plugin_dir = os.join(application.extensions['plugin_manager'].plugin_folder, 'testing_plugin')
    assert os.path.exists(plugin_dir)
    assert os.path.isdir(plugin_dir)
    assert __import__('flaskbb.plugins.testing_plugin').__plugin__=='TestingPlugin'

