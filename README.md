# FlaskBB

[![Build Status](https://travis-ci.org/sh4nks/flaskbb.svg?branch=master)](https://travis-ci.org/sh4nks/flaskbb)
[![Coverage Status](https://coveralls.io/repos/sh4nks/flaskbb/badge.png)](https://coveralls.io/r/sh4nks/flaskbb)
[![Code Health](https://landscape.io/github/sh4nks/flaskbb/master/landscape.svg?style=flat)](https://landscape.io/github/sh4nks/flaskbb/master)
[![License](https://img.shields.io/badge/license-BSD-blue.svg)](https://flaskbb.org)
[![flaskbb@freenode](https://img.shields.io/badge/irc.freenode.net-%23flaskbb-blue.svg)](https://webchat.freenode.net/?channels=flaskbb)

*FlaskBB is a Forum Software written in Python using the micro framework Flask.*

Currently, following features are implemented:

* Private Messages
* Admin Interface
* Group based permissions
* Markdown Support
* Topic Tracker
* Unread Topics/Forums
* i18n Support
* Completely Themeable
* Plugin System
* Command Line Interface

Checkout the [FlaskBB Forums](https://forums.flaskbb.org) to see an actual
running instance of FlaskBB. Use demo//demo as login for the test user.


## Quickstart

For a complete installation guide please visit the installation documentation
[here](https://flaskbb.readthedocs.org/en/latest/installation.html).

This is how you set up an development instance of FlaskBB:

* Create a virtualenv
* Configuration
    * `make devconfig`
* Install dependencies and FlaskBB
    * `make install`
* Run the development server
    * `make run`
* Visit [localhost:5000](http://localhost:5000)


## License

FlaskBB is licensed under the [BSD License](https://github.com/sh4nks/flaskbb/blob/master/LICENSE).


# Links

* [Project Website](https://flaskbb.org)
* [Documentation](https://flaskbb.readthedocs.io)
* [Source Code](https://github.com/sh4nks/flaskbb)
