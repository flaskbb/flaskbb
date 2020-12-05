#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import find_packages, setup


def read(*parts):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


long_description = read("README.md")
install_requires = [
    "alembic>=1.4.3",
    "amqp>=5.0.2",
    "attrs>=20.3.0",
    "Babel>=2.9.0",
    "billiard>=3.6.3.0",
    "blinker>=1.4",
    "celery>=5.0.2",
    "certifi>=2020.11.8",
    "chardet>=3.0.4",
    "click>=7.1.2",
    "click-log>=0.3.2",
    "dnspython>=2.0.0",
    "email-validator>=1.1.2",
    "Flask>=1.1.2",
    "Flask-Alembic>=2.0.1",
    "flask-allows @ git+https://github.com/justanr/flask-allows.git@f/Cut-down-on-warnings#egg=flask-allows",
    "Flask-BabelPlus>=2.2.0",
    "Flask-Caching>=1.9.0",
    "Flask-DebugToolbar>=0.11.0",
    "flask-debugtoolbar-warnings>=0.1.0",
    "Flask-Limiter>=1.4",
    "Flask-Login>=0.5.0",
    "Flask-Mail>=0.9.1",
    "flask-redis>=0.4.0",
    "Flask-SQLAlchemy>=2.4.4",
    "Flask-Themes2>=0.1.5",
    "flask-whooshee>=0.7.0",
    "Flask-WTF>=0.14.3",
    "flaskbb-plugin-conversations>=1.0.7",
    "flaskbb-plugin-portal>=1.1.3",
    "future>=0.18.2",
    "idna>=2.10",
    "itsdangerous>=1.1.0",
    "Jinja2>=2.11.2",
    "kombu>=5.0.2",
    "limits>=1.5.1",
    "Mako>=1.1.3",
    "MarkupSafe>=1.1.1",
    "mistune>=0.8.4",
    "olefile>=0.46",
    "Pillow>=8.0.1",
    "pluggy>=0.13.1",
    "Pygments>=2.7.2",
    "python-dateutil>=2.8.1",
    "python-editor>=1.0.4",
    "pytz>=2020.4",
    "redis>=3.5.3",
    "requests>=2.25.0",
    "simplejson>=3.17.2",
    "six>=1.15.0",
    "speaklater>=1.3",
    "SQLAlchemy>=1.3.20",
    "SQLAlchemy-Utils>=0.36.8",
    "Unidecode>=1.1.1",
    "urllib3>=1.26.2",
    "vine>=5.0.0",
    "Werkzeug>=1.0.1",
    "Whoosh>=2.7.4",
    "WTForms>=2.3.3",
    "WTForms-SQLAlchemy>=0.2",
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
    python_requires=">3.5",
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
