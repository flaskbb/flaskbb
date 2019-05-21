# FlaskBB

[![Build Status](https://dev.azure.com/flaskbb/flaskbb/_apis/build/status/flaskbb.flaskbb?branchName=master)](https://dev.azure.com/flaskbb/flaskbb/_build/latest?definitionId=1&branchName=master)
[![codecov](https://codecov.io/gh/flaskbb/flaskbb/branch/master/graph/badge.svg)](https://codecov.io/gh/flaskbb/flaskbb)
[![requires](https://requires.io/github/flaskbb/flaskbb/requirements.svg?branch=master)](https://requires.io/github/flaskbb/flaskbb/requirements/?branch=master)
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

Feel free to checkout it's feature on our testing instance over at
[test.flaskbb.org](https://test.flaskbb.org). You can use the demo user (``demo//demo``) to
avoid the registration process.

The official forums where all the fun happens can be reached via [forums.flaskbb.org](https://forums.flaskbb.org).


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

FlaskBB is licensed under the [BSD License](https://github.com/flaskbb/flaskbb/blob/master/LICENSE).


# Links

* [Project Website](https://flaskbb.org)
* [Documentation](https://flaskbb.readthedocs.io)
* [Source Code](https://github.com/flaskbb/flaskbb)
