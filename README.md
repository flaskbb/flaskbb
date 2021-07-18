# FlaskBB

[![Build Status](https://github.com/flaskbb/flaskbb/actions/workflows/tests.yml/badge.svg)](https://github.com/flaskbb/flaskbb/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/flaskbb/flaskbb/branch/master/graph/badge.svg)](https://codecov.io/gh/flaskbb/flaskbb)
[![requires](https://requires.io/github/flaskbb/flaskbb/requirements.svg?branch=master)](https://requires.io/github/flaskbb/flaskbb/requirements/?branch=master)
[![License](https://img.shields.io/badge/license-BSD-blue.svg)](https://flaskbb.org)
[![#flaskbb:matrix.org](https://img.shields.io/badge/[matrix]-%23flaskbb%3Amatrix.org-blue)](https://matrix.to/#/#flaskbb:matrix.org)
[![#flaskbb@libera.chat](https://img.shields.io/badge/irc.libera.chat-%23flaskbb-blue.svg)](https://web.libera.chat/?channel=#flaskbb)

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


The official forums which are powered by FlaskBB can be reached via
[forums.flaskbb.org](https://forums.flaskbb.org).


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
