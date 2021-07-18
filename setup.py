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
    "alembic>=1.6.5",
    "amqp>=5.0.6",
    "attrs>=21.2.0",
    "Babel>=2.9.1",
    "billiard>=3.6.4.0",
    "blinker>=1.4",
    "celery>=5.1.2",
    "certifi>=2021.5.30",
    "charset-normalizer>=2.0.3",
    "click>=7.1.2",
    "click-didyoumean>=0.0.3",
    "click-log>=0.3.2",
    "click-plugins>=1.1.1",
    "click-repl>=0.2.0",
    "dnspython>=2.1.0",
    "email-validator>=1.1.3",
    "Flask>=2.0.1",
    "Flask-Alembic>=2.0.1",
    "flask-allows @ git+https://github.com/flaskbb/flask-allows.git@master#egg=flask-allows",
    "Flask-BabelPlus>=2.2.0",
    "Flask-Caching>=1.10.1",
    "Flask-DebugToolbar>=0.11.0",
    "flask-debugtoolbar-warnings>=0.1.0",
    "Flask-Limiter>=1.4",
    "Flask-Login>=0.5.0",
    "Flask-Mail>=0.9.1",
    "flask-redis>=0.4.0",
    "Flask-SQLAlchemy>=2.5.1",
    "Flask-Themes2>=1.0.0",
    "flask-whooshee>=0.8.1",
    "Flask-WTF>=0.15.1",
    "flaskbb-plugin-conversations>=1.0.8",
    "flaskbb-plugin-portal>=1.1.3",
    "greenlet>=1.1.0",
    "idna>=3.2",
    "itsdangerous>=2.0.1",
    "Jinja2>=3.0.1",
    "kombu>=5.1.0",
    "limits>=1.5.1",
    "Mako>=1.1.4",
    "MarkupSafe>=2.0.1",
    "mistune>=0.8.4",
    "Pillow>=8.3.1",
    "pluggy>=0.13.1",
    "prompt-toolkit>=3.0.19",
    "Pygments>=2.9.0",
    "python-dateutil>=2.8.2",
    "python-editor>=1.0.4",
    "pytz>=2021.1",
    "redis>=3.5.3",
    "requests>=2.26.0",
    "six>=1.16.0",
    "SQLAlchemy>=1.4.21",
    "SQLAlchemy-Utils>=0.37.8",
    "Unidecode>=1.2.0",
    "urllib3>=1.26.6",
    "vine>=5.0.0",
    "wcwidth>=0.2.5",
    "Werkzeug>=2.0.1",
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
