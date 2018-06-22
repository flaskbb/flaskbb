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
    "alembic",
    "amqp",
    "attrs",
    "Babel",
    "billiard",
    "blinker",
    "celery",
    "certifi",
    "chardet",
    "click",
    "click-log",
    "enum34",
    "Flask",
    "Flask-Alembic",
    "flask-allows",
    "Flask-BabelPlus",
    "Flask-Caching",
    "Flask-DebugToolbar",
    "flask-debugtoolbar-warnings",
    "Flask-Limiter",
    "Flask-Login",
    "Flask-Mail",
    "Flask-Redis",
    "Flask-SQLAlchemy",
    "Flask-Themes2",
    "flask-whooshee",
    "Flask-WTF",
    "flaskbb-plugin-conversations",
    "flaskbb-plugin-portal",
    "idna",
    "itsdangerous",
    "Jinja2",
    "kombu",
    "limits",
    "Mako",
    "MarkupSafe",
    "mistune",
    "olefile",
    "Pillow",
    "pluggy",
    "Pygments",
    "python-dateutil",
    "python-editor",
    "pytz",
    "redis",
    "requests",
    "simplejson",
    "six",
    "speaklater",
    "SQLAlchemy",
    "SQLAlchemy-Utils",
    "Unidecode",
    "urllib3",
    "vine",
    "Werkzeug",
    "Whoosh",
    "WTForms",
]

extras_require = {"postgres": ["psycopg2-binary"]}

tests_require = ["py", "pytest", "pytest-cov", "cov-core", "coverage"]

setup(
    name="FlaskBB",
    version="2.0.1",
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
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    cmdclass={"test": PyTestCommand},
)
