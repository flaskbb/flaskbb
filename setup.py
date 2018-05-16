#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand


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
        import pytest  # noqa
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


def read(*parts):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def get_requirements(e=None):
    rf = "requirements.txt" if e is None else 'requirements-{}.txt'.format(e)
    r = read(rf)
    return [x.strip() for x in r.split('\n')
            if not x.startswith('#') and not x.startswith("-e")]


long_description = read("README.md")
install_requires = get_requirements()


setup(
    name='FlaskBB',
    version="2.0.0",
    url='https://flaskbb.org',
    project_urls={
        'Documentation': 'https://flaskbb.readthedocs.io/en/latest/',
        'Code': 'https://github.com/flaskbb/flaskbb',
        'Issue Tracker': 'https://github.com/flaskbb/flaskbb',
    },
    license='BSD',
    author='Peter Justin',
    author_email='peter.justin@outlook.com',
    description='A classic Forum Software in Python using Flask.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    entry_points='''
        [console_scripts]
        flaskbb=flaskbb.cli:flaskbb
    ''',
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    install_requires=install_requires,
    tests_require=[
        'py',
        'pytest',
        'pytest-cov',
        'cov-core',
        'coverage'
    ],
    test_suite='tests',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    cmdclass={'test': PyTestCommand}
)
