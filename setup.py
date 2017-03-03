"""
FlaskBB
=======

FlaskBB is a forum software written in Python using the microframework Flask.


And Easy to Setup
-----------------

.. code:: bash
    $ pip install -e .

    $ flaskbb install

    $ flaskbb runserver
     * Running on http://localhost:8080/


Resources
---------

* `website <https://flaskbb.org>`_
* `source <https://github.com/sh4nks/flaskbb>`_
* `issues <https://github.com/sh4nks/flaskbb/issues>`_
"""
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys


class PyTestCommand(TestCommand):
    user_options = [('pytest-args=', 'a', 'Arguments to pass to py.test')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='FlaskBB',
    version='1.0.dev0',
    url='http://github.com/sh4nks/flaskbb/',
    license='BSD',
    author='Peter Justin',
    author_email='peter.justin@outlook.com',
    description='A classic Forum Software in Python using Flask.',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'alembic',
        'amqp',
        'Babel',
        'billiard',
        'blinker',
        'celery',
        'click',
        'Flask',
        'flask-allows',
        'Flask-BabelPlus',
        'Flask-Caching',
        'Flask-DebugToolbar',
        'Flask-Limiter',
        'Flask-Login',
        'Flask-Mail',
        'Flask-Migrate',
        'Flask-Plugins',
        'Flask-Redis',
        'Flask-SQLAlchemy',
        'Flask-Themes2',
        'flask-whooshee',
        'Flask-WTF',
        'itsdangerous',
        'Jinja2',
        'kombu',
        'limits',
        'Mako',
        'MarkupSafe',
        'mistune',
        'Pillow',
        'Pygments',
        'python-editor',
        'pytz',
        'redis',
        'requests',
        'simplejson',
        'six',
        'speaklater',
        'SQLAlchemy',
        'SQLAlchemy-Utils',
        'Unidecode',
        'Werkzeug',
        'Whoosh',
        'WTForms'
    ],
    entry_points='''
        [console_scripts]
        flaskbb=flaskbb.cli:flaskbb
    ''',
    test_suite='tests',
    tests_require=[
        'py',
        'pytest',
        'pytest-cov',
        'cov-core',
        'coverage'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers, Users',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    cmdclass={'test': PyTestCommand}
)
