[![Build Status](https://travis-ci.org/sh4nks/flaskbb.svg?branch=master)](https://travis-ci.org/sh4nks/flaskbb)
[![Coverage Status](https://coveralls.io/repos/sh4nks/flaskbb/badge.png)](https://coveralls.io/r/sh4nks/flaskbb)

# INTRODUCTION

[FlaskBB](http://flaskbb.org) is a forum software written in python
using the micro framework Flask.


**_Note:_** Do not expect too much activity during the summer holidays - I hope you can understand this :)


## FEATURES

* A Bulletin Board like FluxBB or DjangoBB in Flask
* Private Messages
* Admin Interface
* Group based permissions
* BBCode support
* Topic Tracker
* Unread Topics/Forums


## TODO

* See the github [issues](https://github.com/sh4nks/flaskbb/issues?state=open)


## INSTALLATION

* Create a virtualenv
* Install the dependencies
    * `pip install -r requirements.txt`
* Configuration (_adjust them accordingly to your needs_)
    * For development copy `flaskbb/configs/development.py.example` to `flaskbb/configs/development.py`
* Database creation
    * `python manage.py createall`
* Run the development server
    * `python manage.py runserver`
* Visit [localhost:8080](http://localhost:8080)


## DOCUMENTATION

The documentation is located [here](http://flaskbb.readthedocs.org/en/latest/).


## LICENSE

[BSD LICENSE](http://flask.pocoo.org/docs/license/#flask-license)


## ACKNOWLEDGEMENTS

[/r/flask](http://reddit.com/r/flask), [Flask](http://flask.pocoo.org), it's [extensions](http://flask.pocoo.org/extensions/) and everyone who has helped me!
