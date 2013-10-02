from flask import current_app
from flaskbb.helpers import time_diff, time_delta_format, check_perm

def format_date(value, format='%Y-%m-%d'):
    """
    Returns a formatted time string
    """
    return value.strftime(format)

def time_since(value):
    return time_delta_format(value)

def is_online(user):
    return user.lastseen >= time_diff()

def is_current_user(user, post):
    """
    Check if the post is written by the user
    """
    return post.user_id == user.id

def edit_post(user, post, forum):
    """
    Check if the post can be edited by the user
    """
    return check_perm(user, 'deletepost', forum, post.user_id)

def delete_post(user, post, forum):
    """
    Check if the post can be edited by the user
    """
    return check_perm(user, 'deletepost', forum, post.user_id)


def delete_topic(user, post, forum):
    """
    Check if the topic can be deleted by the user
    """
    return check_perm(user, 'deletetopic', forum, post.user_id)


def post_reply(user, forum):
    """
    Check if the user is allowed to post in the forum
    """
    return check_perm(user, 'postreply', forum)


def crop_title(title):
    """
    Crops the title to a specified length
    """
    length = current_app.config['TITLE_LENGTH']
    if len(title) > length:
        return title[:length] + "..."
    return title
