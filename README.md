# INTRODUCTION

[FlaskBB](http://flaskbb.org) is a forum software written in python
using the micro framework Flask.


## FEATURES

* A Bulletin Board like FluxBB, DjangoBB in Flask
* Private Messages
* Admin Interface
* Group based permissions
* BBCode support
* Topic Tracker
* Unread Topics/Forums


## TODO

* Searching for members, posts,...
* ~~"Link to"-Forum type~~
* ~~Move a topic in a other forum~~
* Merging 2 topics together
* ~~Reporting posts~~
* Userstyles (e.q.: colored username)
* ~~Database migrations~~
* A own theme ~~and make FlaskBB themable with Flask-Themes2~~
* Localization (Babel)
* Polls


## DEPENDENCIES

* [Flask](http://flask.pocoo.org)
    * [Werkzeug](http://werkzeug.pocoo.org)
    * [Jinja2](http://jinja.pocoo.org)
* [Flask-SQLAlchemy](http://pythonhosted.org/Flask-SQLAlchemy/)
    * [SQLAlchemy](http://www.sqlalchemy.org/)
* [Flask-WTF](http://pythonhosted.org/Flask-WTF/)
    * [WTForms](http://wtforms.simplecodes.com/docs/1.0.4/)
* [Flask-Login](http://flask-login.readthedocs.org/en/latest/)
* [Flask-Mail](http://pythonhosted.org/flask-mail/)
* [Flask-Script](http://flask-script.readthedocs.org/en/latest/)
* [Flask-Themes2](http://flask-themes2.rtfd.org/)
* [Flask-Migrate](http://flask-migrate.readthedocs.org/en/latest/)


### OPTIONAL DEPENDENCIES

* [Pygmens](http://pygments.org/) - For code highlighting
* [Redis](http://redis.io/) - For counting the online guests


## INSTALLATION

* Create a virtualenv
    * Install virtualenvwrapper with your package manager or via
        * `sudo pip install virtualenvwrapper`
    * Add these lines to your `.bashrc`
            export WORKON_HOME=$HOME/.virtualenvs  # Location for your virtualenvs
            source /usr/local/bin/virtualenvwrapper.sh
    * Create a new virtualenv
        * `mkvirtualenv -a /path/to/flaskbb -p $(which python2) flaskbb`
    * and finally activate it
        * `workon flaskbb`
    * For more options visit the documentation [here](http://virtualenvwrapper.readthedocs.org/en/latest/index.html).


* Install the dependencies
    * `pip install -r requirements.txt`
    * **NOTE**: If you are using pip 1.5 you need to add these parameters: ``--allow-external postmarkup --allow-unverified postmarkup``
* Configuration (_adjust them accordingly to your needs_)
    * For development copy `flaskbb/configs/development.py.example` to `flaskbb/configs/development.py`
    * For production copy `flaskbb/configs/production.py.example` to `flaskbb/configs/production.py`
* Database creation
    * **Development:** Create the database with some example content
        * `python manage.py createall`
    * **Production:** Create the database and the admin user
        * `python manage.py initflaskbb`
* Run the development server
    * `python manage.py runserver`
* Visit [localhost:8080](http://localhost:8080)


## Upgrading

* Upgrading from a previous installation
    * Pull the latest changes from the repository
    * `git pull`
* See if the example config has changed and adjust the settings to your needs
    * `diff flaskbb/configs/production.py flaskbb/configs/production.py.example`
    * `$EDITOR flaskbb/configs/production.py`
* Upgrade the database to the latest revision
    * `python manage.py db upgrade head`


## LICENSE

[BSD LICENSE](http://flask.pocoo.org/docs/license/#flask-license)


## ACKNOWLEDGEMENTS

[/r/flask](http://reddit.com/r/flask), [Flask](http://flask.pocoo.org) and it's [extensions](http://flask.pocoo.org/extensions/).
