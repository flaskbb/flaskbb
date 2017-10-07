# -*- coding: utf-8 -*-
"""
    flaskbb.utils.helpers
    ~~~~~~~~~~~~~~~~~~~~~

    A few helpers that are used by flaskbb

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import ast
import itertools
import operator
import os
import re
import time
from datetime import datetime, timedelta
from email import message_from_string
from functools import wraps

from pkg_resources import get_distribution

import requests
import unidecode
from babel.core import get_locale_identifier
from babel.dates import format_timedelta as babel_format_timedelta
from flask import flash, g, redirect, request, session, url_for
from flask_allows import Permission
from flask_babelplus import lazy_gettext as _
from flask_login import current_user
from flask_themes2 import get_themes_list, render_theme_template
from flaskbb._compat import (iteritems, range_method, text_type, to_bytes,
                             to_unicode)
from flaskbb.extensions import babel, redis_store
from flaskbb.utils.markup import markdown
from flaskbb.utils.settings import flaskbb_config
from jinja2 import Markup
from PIL import ImageFile
from pytz import UTC
from werkzeug.local import LocalProxy

_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text, delim=u'-'):
    """Generates an slightly worse ASCII-only slug.
    Taken from the Flask Snippets page.

   :param text: The text which should be slugified
   :param delim: Default "-". The delimeter for whitespace
    """
    text = unidecode.unidecode(text)
    result = []
    for word in _punct_re.split(text.lower()):
        if word:
            result.append(word)
    return text_type(delim.join(result))


def redirect_or_next(endpoint, **kwargs):
    """Redirects the user back to the page they were viewing or to a specified
    endpoint. Wraps Flasks :func:`Flask.redirect` function.

    :param endpoint: The fallback endpoint.
    """
    return redirect(
        request.args.get('next') or endpoint, **kwargs
    )


def render_template(template, **context):  # pragma: no cover
    """A helper function that uses the `render_theme_template` function
    without needing to edit all the views
    """
    if current_user.is_authenticated and current_user.theme:
        theme = current_user.theme
    else:
        theme = session.get('theme', flaskbb_config['DEFAULT_THEME'])
    return render_theme_template(theme, template, **context)


def do_topic_action(topics, user, action, reverse):
    """Executes a specific action for topics. Returns a list with the modified
    topic objects.

    :param topics: A iterable with ``Topic`` objects.
    :param user: The user object which wants to perform the action.
    :param action: One of the following actions: locked, important and delete.
    :param reverse: If the action should be done in a reversed way.
                    For example, to unlock a topic, ``reverse`` should be
                    set to ``True``.
    """
    if not topics:
        return False

    from flaskbb.utils.requirements import (IsAtleastModeratorInForum,
                                            CanDeleteTopic, Has)

    if not Permission(IsAtleastModeratorInForum(forum=topics[0].forum)):
        flash(_("You do not have the permissions to execute this "
                "action."), "danger")
        return False

    modified_topics = 0
    if action not in {'delete', 'hide', 'unhide'}:
        for topic in topics:
            if getattr(topic, action) and not reverse:
                continue

            setattr(topic, action, not reverse)
            modified_topics += 1
            topic.save()

    elif action == "delete":
        if not Permission(CanDeleteTopic):
            flash(_("You do not have the permissions to delete these topics."), "danger")
            return False

        for topic in topics:
            modified_topics += 1
            topic.delete()

    elif action == 'hide':
        if not Permission(Has('makehidden')):
            flash(_("You do not have the permissions to hide these topics."), "danger")
            return False

        for topic in topics:
            if topic.hidden:
                continue
            modified_topics += 1
            topic.hide(user)

    elif action == 'unhide':
        if not Permission(Has('makehidden')):
            flash(_("You do not have the permissions to unhide these topics."), "danger")
            return False

        for topic in topics:
            if not topic.hidden:
                continue
            modified_topics += 1
            topic.unhide()

    return modified_topics


def get_categories_and_forums(query_result, user):
    """Returns a list with categories. Every category has a list for all
    their associated forums.

    The structure looks like this::
        [(<Category 1>,
          [(<Forum 1>, None),
           (<Forum 2>, <flaskbb.forum.models.ForumsRead at 0x38fdb50>)]),
         (<Category 2>,
          [(<Forum 3>, None),
          (<Forum 4>, None)])]

    and to unpack the values you can do this::
        In [110]: for category, forums in x:
           .....:     print category
           .....:     for forum, forumsread in forums:
           .....:         print "\t", forum, forumsread

   This will print something like this:
        <Category 1>
            <Forum 1> None
            <Forum 2> <flaskbb.forum.models.ForumsRead object at 0x38fdb50>
        <Category 2>
            <Forum 3> None
            <Forum 4> None

    :param query_result: A tuple (KeyedTuple) with all categories and forums

    :param user: The user object is needed because a signed out user does not
                 have the ForumsRead relation joined.
    """
    it = itertools.groupby(query_result, operator.itemgetter(0))

    forums = []

    if user.is_authenticated:
        for key, value in it:
            forums.append((key, [(item[1], item[2]) for item in value]))
    else:
        for key, value in it:
            forums.append((key, [(item[1], None) for item in value]))

    return forums


def get_forums(query_result, user):
    """Returns a tuple which contains the category and the forums as list.
    This is the counterpart for get_categories_and_forums and especially
    usefull when you just need the forums for one category.

    For example::
        (<Category 2>,
          [(<Forum 3>, None),
          (<Forum 4>, None)])

    :param query_result: A tuple (KeyedTuple) with all categories and forums

    :param user: The user object is needed because a signed out user does not
                 have the ForumsRead relation joined.
    """
    it = itertools.groupby(query_result, operator.itemgetter(0))

    if user.is_authenticated:
        for key, value in it:
            forums = key, [(item[1], item[2]) for item in value]
    else:
        for key, value in it:
            forums = key, [(item[1], None) for item in value]

    return forums


def forum_is_unread(forum, forumsread, user):
    """Checks if a forum is unread

    :param forum: The forum that should be checked if it is unread

    :param forumsread: The forumsread object for the forum

    :param user: The user who should be checked if he has read the forum
    """
    # If the user is not signed in, every forum is marked as read
    if not user.is_authenticated:
        return False

    read_cutoff = time_utcnow() - timedelta(
        days=flaskbb_config["TRACKER_LENGTH"])

    # disable tracker if TRACKER_LENGTH is set to 0
    if flaskbb_config["TRACKER_LENGTH"] == 0:
        return False

    # If there are no topics in the forum, mark it as read
    if forum and forum.topic_count == 0:
        return False

    # check if the last post is newer than the tracker length
    if forum.last_post_id is None or forum.last_post_created < read_cutoff:
        return False

    # If the user hasn't visited a topic in the forum - therefore,
    # forumsread is None and we need to check if it is still unread
    if forum and not forumsread:
        return forum.last_post_created > read_cutoff

    try:
        # check if the forum has been cleared and if there is a new post
        # since it have been cleared
        if forum.last_post_created > forumsread.cleared:
            if forum.last_post_created < forumsread.last_read:
                return False
    except TypeError:
        pass

    # else just check if the user has read the last post
    return forum.last_post_created > forumsread.last_read


def topic_is_unread(topic, topicsread, user, forumsread=None):
    """Checks if a topic is unread.

    :param topic: The topic that should be checked if it is unread

    :param topicsread: The topicsread object for the topic

    :param user: The user who should be checked if he has read the last post
                 in the topic

    :param forumsread: The forumsread object in which the topic is. If you
                       also want to check if the user has marked the forum as
                       read, than you will also need to pass an forumsread
                       object.
    """
    if not user.is_authenticated:
        return False

    read_cutoff = time_utcnow() - timedelta(
        days=flaskbb_config["TRACKER_LENGTH"])

    # disable tracker if read_cutoff is set to 0
    if flaskbb_config["TRACKER_LENGTH"] == 0:
        return False

    # check read_cutoff
    if topic.last_post.date_created < read_cutoff:
        return False

    # topicsread is none if the user has marked the forum as read
    # or if he hasn't visited the topic yet
    if topicsread is None:
        # user has cleared the forum - check if there is a new post
        if forumsread and forumsread.cleared is not None:
            return forumsread.cleared < topic.last_post.date_created

        # user hasn't read the topic yet, or there is a new post since the user
        # has marked the forum as read
        return True

    # check if there is a new post since the user's last topic visit
    return topicsread.last_read < topic.last_post.date_created


def mark_online(user_id, guest=False):  # pragma: no cover
    """Marks a user as online

    :param user_id: The id from the user who should be marked as online

    :param guest: If set to True, it will add the user to the guest activity
                  instead of the user activity.

    Ref: http://flask.pocoo.org/snippets/71/
    """
    user_id = to_bytes(user_id)
    now = int(time.time())
    expires = now + (flaskbb_config['ONLINE_LAST_MINUTES'] * 60) + 10
    if guest:
        all_users_key = 'online-guests/%d' % (now // 60)
        user_key = 'guest-activity/%s' % user_id
    else:
        all_users_key = 'online-users/%d' % (now // 60)
        user_key = 'user-activity/%s' % user_id
    p = redis_store.pipeline()
    p.sadd(all_users_key, user_id)
    p.set(user_key, now)
    p.expireat(all_users_key, expires)
    p.expireat(user_key, expires)
    p.execute()


def get_online_users(guest=False):  # pragma: no cover
    """Returns all online users within a specified time range

    :param guest: If True, it will return the online guests
    """
    current = int(time.time()) // 60
    minutes = range_method(flaskbb_config['ONLINE_LAST_MINUTES'])
    if guest:
        users = redis_store.sunion(['online-guests/%d' % (current - x)
                                   for x in minutes])
    else:
        users = redis_store.sunion(['online-users/%d' % (current - x)
                                   for x in minutes])

    return [to_unicode(u) for u in users]


def crop_title(title, length=None, suffix="..."):
    """Crops the title to a specified length

    :param title: The title that should be cropped

    :param suffix: The suffix which should be appended at the
                   end of the title.
    """
    length = flaskbb_config['TITLE_LENGTH'] if length is None else length

    if len(title) <= length:
        return title

    return title[:length].rsplit(' ', 1)[0] + suffix


def render_markup(text):
    """Renders the given text as markdown

    :param text: The text that should be rendered as markdown
    """
    return Markup(markdown.render(text))


def is_online(user):
    """A simple check to see if the user was online within a specified
    time range

    :param user: The user who needs to be checked
    """
    return user.lastseen >= time_diff()


def time_utcnow():
    """Returns a timezone aware utc timestamp."""
    return datetime.now(UTC)


def time_diff():
    """Calculates the time difference between now and the ONLINE_LAST_MINUTES
    variable from the configuration.
    """
    now = time_utcnow()
    diff = now - timedelta(minutes=flaskbb_config['ONLINE_LAST_MINUTES'])
    return diff


def format_date(value, format='%Y-%m-%d'):
    """Returns a formatted time string

    :param value: The datetime object that should be formatted

    :param format: How the result should look like. A full list of available
                   directives is here: http://goo.gl/gNxMHE
    """
    return value.strftime(format)


def format_timedelta(delta, **kwargs):
    """Wrapper around babel's format_timedelta to make it user language
    aware.
    """
    locale = flaskbb_config.get("DEFAULT_LANGUAGE", "en")
    if current_user.is_authenticated and current_user.language is not None:
        locale = current_user.language

    return babel_format_timedelta(delta, locale=locale, **kwargs)


def time_since(time):  # pragma: no cover
    """Returns a string representing time since e.g.
    3 days ago, 5 hours ago.

    :param time: A datetime object
    """
    delta = time - time_utcnow()
    return format_timedelta(delta, add_direction=True)


def format_quote(username, content):
    """Returns a formatted quote depending on the markup language.

    :param username: The username of a user.
    :param content: The content of the quote
    """
    profile_url = url_for('user.profile', username=username)
    content = "\n> ".join(content.strip().split('\n'))
    quote = u"**[{username}]({profile_url}) wrote:**\n> {content}\n".\
            format(username=username, profile_url=profile_url, content=content)

    return quote


def get_image_info(url):
    """Returns the content-type, image size (kb), height and width of
    an image without fully downloading it.

    :param url: The URL of the image.
    """
    r = requests.get(url, stream=True)
    image_size = r.headers.get("content-length")
    image_size = float(image_size) / 1000  # in kilobyte
    image_max_size = 10000
    image_data = {
        "content_type": "",
        "size": image_size,
        "width": 0,
        "height": 0
    }

    # lets set a hard limit of 10MB
    if image_size > image_max_size:
        return image_data

    data = None
    parser = ImageFile.Parser()

    while True:
        data = r.raw.read(1024)
        if not data:
            break

        parser.feed(data)
        if parser.image:
            image_data["content_type"] = parser.image.format
            image_data["width"] = parser.image.size[0]
            image_data["height"] = parser.image.size[1]
            break

    return image_data


def check_image(url):
    """A little wrapper for the :func:`get_image_info` function.
    If the image doesn't match the ``flaskbb_config`` settings it will
    return a tuple with a the first value is the custom error message and
    the second value ``False`` for not passing the check.
    If the check is successful, it will return ``None`` for the error message
    and ``True`` for the passed check.

    :param url: The image url to be checked.
    """
    img_info = get_image_info(url)
    error = None

    if img_info["size"] > flaskbb_config["AVATAR_SIZE"]:
        error = "Image is too big! {}kb are allowed.".format(
            flaskbb_config["AVATAR_SIZE"]
        )
        return error, False

    if not img_info["content_type"] in flaskbb_config["AVATAR_TYPES"]:
        error = "Image type {} is not allowed. Allowed types are: {}".format(
            img_info["content_type"],
            ", ".join(flaskbb_config["AVATAR_TYPES"])
        )
        return error, False

    if img_info["width"] > flaskbb_config["AVATAR_WIDTH"]:
        error = "Image is too wide! {}px width is allowed.".format(
            flaskbb_config["AVATAR_WIDTH"]
        )
        return error, False

    if img_info["height"] > flaskbb_config["AVATAR_HEIGHT"]:
        error = "Image is too high! {}px height is allowed.".format(
            flaskbb_config["AVATAR_HEIGHT"]
        )
        return error, False

    return error, True


def get_alembic_locations(plugin_dirs):
    """Returns a tuple with (branchname, plugin_dir) combinations.
    The branchname is the name of plugin directory which should also be
    the unique identifier of the plugin.
    """
    branches_dirs = [
        tuple([os.path.basename(os.path.dirname(p)), p])
        for p in plugin_dirs
    ]

    return branches_dirs


def get_available_themes():
    """Returns a list that contains all available themes. The items in the
    list are tuples where the first item of the tuple is the identifier and
    the second one the name of the theme.
    For example::

        [('aurora_mod', 'Aurora Mod')]
    """
    return [(theme.identifier, theme.name) for theme in get_themes_list()]


def get_available_languages():
    """Returns a list that contains all available languages. The items in the
    list are tuples where the first item of the tuple is the locale
    identifier (i.e. de_AT) and the second one the display name of the locale.
    For example::

        [('de_AT', 'Deutsch (Österreich)')]
    """
    return [
        (get_locale_identifier((l.language, l.territory)), l.display_name)
        for l in babel.list_translations()
    ]


def app_config_from_env(app, prefix="FLASKBB_"):
    """Retrieves the configuration variables from the environment.
    Set your environment variables like this::

        export FLASKBB_SECRET_KEY="your-secret-key"

    and based on the prefix, it will set the actual config variable
    on the ``app.config`` object.

    :param app: The application object.
    :param prefix: The prefix of the environment variables.
    """
    for key, value in iteritems(os.environ):
        if key.startswith(prefix):
            key = key[len(prefix):]
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                pass
            app.config[key] = value
    return app


class ReverseProxyPathFix(object):
    """Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.
    http://flask.pocoo.org/snippets/35/

    In wsgi.py::

        from flaskbb.utils.helpers import ReverseProxyPathFix
        flaskbb = create_app(config="flaskbb.cfg")
        flaskbb.wsgi_app = ReverseProxyPathFix(flaskbb.wsgi_app)

    and in nginx::

        location /forums {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Scheme $scheme;
            proxy_set_header X-Script-Name /forums;  # this part here
        }

    :param app: the WSGI application
    :param force_https: Force HTTPS on all routes. Defaults to ``False``.
    """

    def __init__(self, app, force_https=False):
        self.app = app
        self.force_https = force_https

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ.get('PATH_INFO', '')
            if path_info and path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]
        server = environ.get('HTTP_X_FORWARDED_SERVER_CUSTOM',
                             environ.get('HTTP_X_FORWARDED_SERVER', ''))
        if server:
            environ['HTTP_HOST'] = server

        scheme = environ.get('HTTP_X_SCHEME', '')

        if scheme:
            environ['wsgi.url_scheme'] = scheme

        if self.force_https:
            environ['wsgi.url_scheme'] = 'https'

        return self.app(environ, start_response)


def real(obj):
    """Unwraps a werkzeug.local.LocalProxy object if given one,
    else returns the object.
    """
    if isinstance(obj, LocalProxy):
        return obj._get_current_object()
    return obj


def parse_pkg_metadata(dist_name):
    raw_metadata = get_distribution(dist_name).get_metadata('PKG-INFO')
    metadata = {}

    # lets use the Parser from email to parse our metadata :)
    for key, value in message_from_string(raw_metadata).items():
        metadata[key.replace('-', '_').lower()] = value

    return metadata


def anonymous_required(f):

    @wraps(f)
    def wrapper(*a, **k):
        if current_user is not None and current_user.is_authenticated:
            return redirect_or_next(url_for('forum.index'))
        return f(*a, **k)

    return wrapper


def enforce_recaptcha(limiter):
    current_limit = getattr(g, 'view_rate_limit', None)
    login_recaptcha = False
    if current_limit is not None:
        window_stats = limiter.limiter.get_window_stats(*current_limit)
        stats_diff = flaskbb_config["AUTH_REQUESTS"] - window_stats[1]
        login_recaptcha = stats_diff >= flaskbb_config["LOGIN_RECAPTCHA"]
    return login_recaptcha


def registration_enabled(f):

    @wraps(f)
    def wrapper(*a, **k):
        if not flaskbb_config["REGISTRATION_ENABLED"]:
            flash(_("The registration has been disabled."), "info")
            return redirect_or_next(url_for("forum.index"))
        return f(*a, **k)

    return wrapper


def requires_unactivated(f):

    @wraps(f)
    def wrapper(*a, **k):
        if current_user.is_active or not flaskbb_config["ACTIVATE_ACCOUNT"]:
            flash(_("This account is already activated."), "info")
            return redirect(url_for('forum.index'))
        return f(*a, **k)
    return wrapper


def register_view(bp_or_app, routes, view_func, *args, **kwargs):
    for route in routes:
        bp_or_app.add_url_rule(route, view_func=view_func, *args, **kwargs)
