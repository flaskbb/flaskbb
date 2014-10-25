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
        'Flask',
        'Flask-Redis',
        'Flask-Cache',
        'Flask-DebugToolbar',
        'Flask-Login',
        'Flask-Mail',
        'Flask-Migrate',
        'Flask-Plugins',
        'Flask-SQLAlchemy',
        'Flask-Script',
        'Flask-Themes2',
        'Flask-WTF',
        'Flask-WhooshAlchemy',
        'Jinja2',
        'Mako',
        'MarkupSafe',
        'Pygments',
        'SQLAlchemy',
        'WTForms',
        'Werkzeug',
        'Whoosh',
        'alembic',
        'blinker',
        'itsdangerous',
        'py',
        'pytest',
        'pytest-random',
        'pytest-cov',
        'redis',
        'simplejson',
        'postmarkup',
        'unidecode'
    ],
    dependency_links=[
        'https://github.com/frol/postmarkup/tarball/master#egg=postmarkup',
        'https://github.com/jshipley/Flask-WhooshAlchemy/archive/master.zip#egg=Flask-WhooshAlchemy'
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
