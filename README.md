# INTRODUCTION

[FlaskBB](http://flaskbb.org) is a forum software written in python
using the micro framework Flask.


## FEATURES

* A Bulletin Board like FluxBB, DjangoBB in Flask
* Private Messages
* Admin Interface
* Group based permissions
* BBCode support


## TODO

* Topic Tracker (in progress)
* Track the unread posts and mark them as new
* A own theme and make FlaskBB themable with Flask-Themes2
* Localization (Babel)
* Searching for members, posts,...
* Subforums
* Figure out how to integrate it in another app where you can use the models from flaskbb and so on..


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


## INSTALLATION

* Create a virtualenv
* Install the dependencies with `pip install -r requirements.txt`
* Copy `flaskbb/configs/development.py.example` to `flaskbb/configs/development.py`
* Create the database with some example content `python manage.py createall`
* Run the development server `python manage.py runserver`
* Visit [localhost:8080](http://localhost:8080)

## LICENSE

[BSD LICENSE](http://flask.pocoo.org/docs/license/#flask-license)

## ACKNOWLEDGEMENTS

[/r/flask](http://reddit.com/r/flask), [Flask](http://flask.pocoo.org) and it's [extensions](http://flask.pocoo.org/extensions/).
