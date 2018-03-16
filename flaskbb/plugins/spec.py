# -*- coding: utf-8 -*-
"""
    flaskbb.plugins.spec
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module provides the core FlaskBB plugin hook definitions

    :copyright: (c) 2017 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""

from pluggy import HookspecMarker

spec = HookspecMarker('flaskbb')


# Setup Hooks
@spec
def flaskbb_extensions(app):
    """Hook for initializing any plugin loaded extensions."""


@spec
def flaskbb_load_translations():
    """Hook for registering translation folders."""


@spec
def flaskbb_load_migrations():
    """Hook for registering additional migrations."""


@spec
def flaskbb_load_blueprints(app):
    """Hook for registering blueprints."""


@spec
def flaskbb_request_processors(app):
    """Hook for registering pre/post request processors."""


@spec
def flaskbb_errorhandlers(app):
    """Hook for registering error handlers."""


@spec
def flaskbb_jinja_directives(app):
    """Hook for registering jinja filters, context processors, etc."""


@spec
def flaskbb_additional_setup(app, pluggy):
    """Hook for any additional setup a plugin wants to do after all other
    application setup has finished.

    For example, you could apply a WSGI middleware::

        @impl
        def flaskbb_additional_setup(app):
            app.wsgi_app = ProxyFix(app.wsgi_app)
    """


@spec
def flaskbb_cli(cli):
    """Hook for registering CLI commands."""


@spec
def flaskbb_shell_context():
    """Hook for registering shell context handlers
    Expected to return a single callable function that returns a dictionary or
    iterable of key value pairs.
    """


# Event hooks
@spec
def flaskbb_event_before_post(post):
    """Hook for handling a post before it has been saved.

    :param flaskbb.forum.models.Post post: The post which triggered the event.
    """


@spec
def flaskbb_event_after_post(post, is_new):
    """Hook for handling a post after it has been saved.

    :param flaskbb.forum.models.Post post: The post which triggered the event.
    :param bool is_new: True if the post is new, False if it is an edit.
    """


# Form hooks
@spec
def flaskbb_form_new_post(form):
    """Hook for modyfing the ReplyForm.

    For example::

        @impl
        def flaskbb_form_new_post(form):
            form.example = TextField("Example Field", validators=[
                DataRequired(message="This field is required"),
                Length(min=3, max=50)])

    :param form: The ``ReplyForm`` class.
    """


@spec
def flaskbb_form_new_post_save(form):
    """Hook for modyfing the ReplyForm.

    This hook is called while populating the post object with
    the data from the form. The post object will be saved after the hook
    call.

    :param form: The form object.
    :param post: The post object.
    """


# Template Hooks
@spec
def flaskbb_tpl_navigation_before():
    """Hook for registering additional navigation items.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_navigation_after():
    """Hook for registering additional navigation items.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_user_nav_loggedin_before():
    """Hook for registering additional user navigational items
    which are only shown when a user is logged in.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_user_nav_loggedin_after():
    """Hook for registering additional user navigational items
    which are only shown when a user is logged in.

    in :file:`templates/layout.html`.
    """


@spec
def flaskbb_tpl_form_registration_before(form):
    """This hook is emitted in the Registration form **before** the first
    input field but after the hidden CSRF token field.

    in :file:`templates/auth/register.html`.

    :param form: The form object.
    """


@spec
def flaskbb_tpl_form_registration_after(form):
    """This hook is emitted in the Registration form **after** the last
    input field but before the submit field.

    in :file:`templates/auth/register.html`.

    :param form: The form object.
    """


@spec
def flaskbb_tpl_form_user_details_before(form):
    """This hook is emitted in the Change User Details form **before** an
    input field is rendered.

    in :file:`templates/user/change_user_details.html`.

    :param form: The form object.
    """


@spec
def flaskbb_tpl_form_user_details_after(form):
    """This hook is emitted in the Change User Details form **after** the last
    input field has been rendered but before the submit field.

    in :file:`templates/user/change_user_details.html`.

    :param form: The form object.
    """


@spec
def flaskbb_tpl_profile_settings_menu():
    """This hook is emitted on the user settings page in order to populate the
    side bar menu. Implementations of this hook should return a list of tuples
    that are view name and display text. The display text will be provided to
    the translation service so it is unnecessary to supply translated text.

    A plugin can declare a new block by setting the view to None. If this is
    done, consider marking the hook implementation with `trylast=True` to
    avoid capturing plugins that do not create new blocks.

    For example::

        @impl(trylast=True)
        def flaskbb_tpl_profile_settings_menu():
            return [
                (None, 'Account Settings'),
                ('user.settings', 'General Settings'),
                ('user.change_user_details', 'Change User Details'),
                ('user.change_email', 'Change E-Mail Address'),
                ('user.change_password', 'Change Password')
            ]

    Hookwrappers for this spec should not be registered as FlaskBB
    supplies its own hookwrapper to flatten all the lists into a single list.

    in :file:`templates/user/settings_layout.html`
    """


@spec
def flaskbb_tpl_admin_settings_menu(user):
    """This hook is emitted in the admin panel and used to add additional
    navigation links to the admin menu.

    Implementations of this hook should return a list of tuples
    that are view name, display text and optionally an icon.
    The display text will be provided to the translation service so it
    is unnecessary to supply translated text.

    For example::

        @impl(hookwrapper=True, tryfirst=True)
        def flaskbb_tpl_admin_settings_menu():
            # only add this item if the user is an admin
            if Permission(IsAdmin, identity=current_user):
                return [
                    ("myplugin.foobar", "Foobar", "fa fa-foobar")
                ]

    Hookwrappers for this spec should not be registered as FlaskBB
    supplies its own hookwrapper to flatten all the lists into a single list.

    in :file:`templates/management/management_layout.html`
    """


@spec
def flaskbb_tpl_profile_sidebar_stats(user):
    """This hook is emitted on the users profile page below the standard
    information. For example, it can be used to add additional items
    such as a link to the profile.

    in :file:`templates/user/profile_layout.html`

    :param user: The user object for whom the profile is currently visited.
    """


@spec
def flaskbb_tpl_post_author_info_before(user, post):
    """This hook is emitted before the information about the
    author of a post is displayed (but after the username).

    in :file:`templates/forum/topic.html`

    :param user: The user object of the post's author.
    :param post: The post object.
    """


@spec
def flaskbb_tpl_post_author_info_after(user, post):
    """This hook is emitted after the information about the
    author of a post is displayed (but after the username).

    in :file:`templates/forum/topic.html`

    :param user: The user object of the post's author.
    :param post: The post object.
    """


@spec
def flaskbb_tpl_post_menu_before(post):
    """Hook for inserting a new item at the beginning of the post menu.

    :param post: The current post object.
    """


@spec
def flaskbb_tpl_post_menu_after(post):
    """Hook for inserting a new item at the end of the post menu.

    :param post: The current post object.
    """


@spec
def flaskbb_tpl_topic_controls(topic):
    """Hook for inserting additional topic moderation controls.

    :param topic: The current topic object.
    """


@spec
def flaskbb_tpl_form_new_post_before(form):
    """Hook for inserting a new form field before the first field is
    rendered.

    For example::

        @impl
        def flaskbb_tpl_form_new_post_after(form):
            return render_template_string(
                \"""
                <div class="form-group">
                    <div class="col-md-12 col-sm-12 col-xs-12">
                        <label>{{ form.example.label.text }}</label>

                        {{ form.example(class="form-control",
                                        placeholder=form.example.label.text) }}

                        {%- for error in form.example.errors -%}
                        <span class="help-block">{{error}}</span>
                        {%- endfor -%}
                    </div>
                </div>
                \"""

    in :file:`templates/forum/new_post.html`

    :param form: The form object.
    """


@spec
def flaskbb_tpl_form_new_post_after(form):
    """Hook for inserting a new form field after the last field is
    rendered (but before the submit field).

    :param form: The form object.
    """
