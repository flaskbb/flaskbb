"""
FlaskBB
=======

FlaskBB is a forum software written in Python using the microframework Flask.


And Easy to Setup
-----------------

.. code:: bash
    $ python manage.py createall

    $ python manage.py runserver
     * Running on http://localhost:8080/


Resources
---------

* `website <http://flaskbb.org>`_
* `source <https://github.com/sh4nks/flaskbb>`_
* `issues <https://github.com/sh4nks/flaskbb/issues>`_

"""
from setuptools import setup

setup(
    name='FlaskBB',
    version='0.1-dev',
    url='http://github.com/sh4nks/flaskbb/',
    license='BSD',
    author='sh4nks',
    author_email='sh4nks7@gmail.com',
    description='A forum software written with flask',
    long_description=__doc__,
    packages=['flaskbb'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Babel',
        'Flask',
        'Flask-Cache',
        'Flask-DebugToolbar',
        'Flask-Login',
        'Flask-Mail',
        'Flask-Migrate',
        'Flask-Plugins',
        'Flask-Redis',
        'Flask-SQLAlchemy',
        'Flask-Script',
        'Flask-Themes2',
        'Flask-WTF',
        'Flask-WhooshAlchemy',
        'Flask-BabelEx',
        'Jinja2',
        'Mako',
        'MarkupSafe',
        'Pygments',
        'SQLAlchemy',
        'Unidecode',
        'WTForms',
        'Werkzeug',
        'Whoosh',
        'alembic',
        'blinker',
        'cov-core',
        'coverage',
        'itsdangerous',
        'mistune',
        'py',
        'pytest',
        'pytest-cov',
        'pytest-random',
        'pytz',
        'redis',
        'requests',
        'simplejson',
        'speaklater',
        'sqlalchemy-utils'
    ],
    dependency_links=[
        'https://github.com/jshipley/Flask-WhooshAlchemy/archive/master.zip#egg=Flask-WhooshAlchemy',
        'https://github.com/sh4nks/flask-babelex/tarball/master#egg=Flask-BabelEx'
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
    ]
)
