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
        'Flask==0.10.1',
        'Flask-And-Redis==0.5',
        'Flask-Cache==0.12',
        'Flask-DebugToolbar==0.9.0',
        'Flask-Login==0.2.10',
        'Flask-Mail==0.9.0',
        'Flask-Migrate==1.2.0',
        'Flask-SQLAlchemy==1.0',
        'Flask-Script==0.6.7',
        'Flask-Themes2==0.1.3',
        'Flask-WTF==0.9.4',
        'Jinja2==2.7.2',
        'Mako==0.9.1',
        'MarkupSafe==0.19',
        'Pygments==1.6',
        'SQLAlchemy==0.9.3',
        'WTForms==1.0.5',
        'Werkzeug==0.9.4',
        'Whoosh==2.6.0',
        'alembic==0.6.3',
        'blinker==1.3',
        'itsdangerous==0.23',
        'postmarkup==1.2.0',
        'redis==2.9.1',
        'simplejson==3.3.3',
        'wsgiref==0.1.2',
        'Flask-WhooshAlchemy'
    ],
    dependency_links=[
        'http://github.com/miguelgrinberg/Flask-WhooshAlchemy/tarball/master#egg=Flask-WhooshAlchemy'
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
