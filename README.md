[![Build Status](https://travis-ci.org/sh4nks/flaskbb.svg?branch=master)](https://travis-ci.org/sh4nks/flaskbb)
[![Coverage Status](https://coveralls.io/repos/sh4nks/flaskbb/badge.png)](https://coveralls.io/r/sh4nks/flaskbb)
[![Code Health](https://landscape.io/github/sh4nks/flaskbb/master/landscape.svg?style=flat)](https://landscape.io/github/sh4nks/flaskbb/master)
[![License](https://img.shields.io/badge/license-BSD-blue.svg)](https://flaskbb.org)

# INTRODUCTION

[FlaskBB](http://flaskbb.org) is a forum software written in python
using the micro framework Flask.


## FEATURES

* A Bulletin Board like FluxBB or DjangoBB in Flask
* Private Messages
* Admin Interface
* Group based permissions
* BBCode Support
* Topic Tracker
* Unread Topics/Forums
* i18n Support
* Completely Themeable
* Plugin System


## TODO

* See the github [issues](https://github.com/sh4nks/flaskbb/issues?state=open)


## INSTALLATION

For a complete installation guide please visit the installation documentation
[here](https://flaskbb.readthedocs.org/en/latest/installation.html).

* Create a virtualenv
* Install the dependencies
    * `pip install -r requirements.txt`
* Configuration (_adjust them accordingly to your needs_)
    * For development copy `flaskbb/configs/development.py.example` to `flaskbb/configs/development.py`
* Create the database & populate it
    * `python manage.py populate`
* Run the development server
    * `python manage.py runserver`
* Visit [localhost:8080](http://localhost:8080)


## DOCUMENTATION

The documentation is located [here](http://flaskbb.readthedocs.org/en/latest/).


## LICENSE

[BSD LICENSE](http://flask.pocoo.org/docs/license/#flask-license)


## ACKNOWLEDGEMENTS

[/r/flask](http://reddit.com/r/flask), [Flask](http://flask.pocoo.org), it's [extensions](http://flask.pocoo.org/extensions/) and everyone who has helped me!
