[![Build Status](https://travis-ci.org/sh4nks/flaskbb.svg?branch=master)](https://travis-ci.org/sh4nks/flaskbb)
[![Coverage Status](https://coveralls.io/repos/sh4nks/flaskbb/badge.png)](https://coveralls.io/r/sh4nks/flaskbb)
[![Code Health](https://landscape.io/github/sh4nks/flaskbb/master/landscape.svg?style=flat)](https://landscape.io/github/sh4nks/flaskbb/master)
[![License](https://img.shields.io/badge/license-BSD-blue.svg)](https://flaskbb.org)

# Introduction

[FlaskBB](http://flaskbb.org) is a forum software written in python
using the micro framework Flask.


## Features

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


## Quickstart

For a complete installation guide please visit the installation documentation
[here](https://flaskbb.readthedocs.org/en/latest/installation.html).

* Create a virtualenv
* Configuration (_adjust them accordingly to your needs_)
    * For development copy `flaskbb/configs/development.py.example` to `flaskbb/configs/development.py`
* Install dependencies and FlaskBB
    * `make install`
* Run the development server
    * `make run`
* Visit [localhost:8080](http://localhost:8080)


## Documentation

The documentation is located [here](http://flaskbb.readthedocs.org/en/latest/).


## License

[BSD LICENSE](http://flask.pocoo.org/docs/license/#flask-license)


## Acknowledgements

[/r/flask](http://reddit.com/r/flask), [Flask](http://flask.pocoo.org), it's [extensions](http://flask.pocoo.org/extensions/) and everyone who has helped me!
