#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand


class PyTestCommand(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest  # noqa

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def read(*parts):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


long_description = read("README.md")
install_requires = [
    "alembic>=0.9.9",
    "amqp>=2.3.2",
    "attrs>=18.1.0",
    "Babel>=2.6.0",
    "billiard>=3.5.0.3",
    "blinker>=1.4",
    "celery>=4.2.0",
    "certifi>=2018.4.16",
    "chardet>=3.0.4",
    "click>=6.7",
    "click-log>=0.3.2",
    "enum34>=1.1.6 ; python_version<'3.4'",
    "Flask>=1.0.2",
    "Flask-Alembic>=2.0.1",
    "flask-allows>=0.6.0",
    "Flask-BabelPlus>=2.1.1",
    "Flask-Caching>=1.4.0",
    "Flask-DebugToolbar>=0.10.1",
    "flask-debugtoolbar-warnings>=0.1.0",
    "Flask-Limiter>=1.0.1",
    "Flask-Login>=0.4.1",
    "Flask-Mail>=0.9.1",
    "Flask-Redis>=0.3.0",
    "Flask-SQLAlchemy>=2.3.2",
    "Flask-Themes2>=0.1.4",
    "flask-whooshee>=0.6.0",
    "Flask-WTF>=0.14.2",
    "flaskbb-plugin-conversations>=1.0.3",
    "flaskbb-plugin-portal>=1.1.1",
    "idna>=2.7",
    "itsdangerous>=0.24",
    "Jinja2>=2.10",
    "kombu>=4.2.1",
    "limits>=1.3",
    "Mako>=1.0.7",
    "MarkupSafe>=1.0",
    "mistune>=0.8.3",
    "olefile>=0.45.1",
    "Pillow>=5.1.0",
    "pluggy>=0.6.0",
    "Pygments>=2.2.0",
    "python-dateutil>=2.7.3",
    "python-editor>=1.0.3",
    "pytz>=2018.4",
    "redis>=2.10.6",
    "requests>=2.19.1",
    "simplejson>=3.15.0",
    "six>=1.11.0",
    "speaklater>=1.3",
    "SQLAlchemy>=1.2.8",
    "SQLAlchemy-Utils>=0.33.3",
    "Unidecode>=1.0.22",
    "urllib3>=1.23",
    "vine>=1.1.4",
    "Werkzeug==0.16.1",
    "Whoosh>=2.7.4",
    "WTForms>=2.2.1",
]

extras_require = {"postgres": ["psycopg2-binary"]}

tests_require = ["py", "pytest", "pytest-cov", "cov-core", "coverage"]

setup(
    name="FlaskBB",
    version="2.0.2",
    url="https://flaskbb.org",
    project_urls={
        "Documentation": "https://flaskbb.readthedocs.io/en/latest/",
        "Code": "https://github.com/flaskbb/flaskbb",
        "Issue Tracker": "https://github.com/flaskbb/flaskbb",
    },
    license="BSD",
    author="Peter Justin",
    author_email="peter.justin@outlook.com",
    description="A classic Forum Software in Python using Flask.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms="any",
    entry_points="""
        [console_scripts]
        flaskbb=flaskbb.cli:flaskbb
    """,
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=tests_require,
    test_suite="tests",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    cmdclass={"test": PyTestCommand},
)
