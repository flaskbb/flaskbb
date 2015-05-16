# -*- coding: utf-8 -*-
"""
    flaskbb.management.views
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module handles the management views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
from datetime import datetime

from flask import (Blueprint, current_app, request, redirect, url_for, flash,
                   __version__ as flask_version)
from flask_login import current_user
from flask_plugins import get_all_plugins, get_plugin, get_plugin_from_all
from flask_babelex import gettext as _

from flaskbb import __version__ as flaskbb_version
from flaskbb._compat import iteritems
from flaskbb.forum.forms import UserSearchForm
from flaskbb.utils.settings import flaskbb_config
from flaskbb.utils.helpers import render_template
from flaskbb.utils.decorators import admin_required, moderator_required
from flaskbb.utils.permissions import can_ban_user, can_edit_user
from flaskbb.extensions import db
from flaskbb.user.models import Guest, User, Group
from flaskbb.forum.models import Post, Topic, Forum, Category, Report
from flaskbb.management.models import Setting, SettingsGroup
from flaskbb.management.forms import (AddUserForm, EditUserForm, AddGroupForm,
                                      EditGroupForm, EditForumForm,
                                      AddForumForm, CategoryForm)


management = Blueprint("management", __name__)


@management.route("/")
@moderator_required
def overview():
    python_version = "%s.%s" % (sys.version_info[0], sys.version_info[1])
    user_count = User.query.count()
    topic_count = Topic.query.count()
    post_count = Post.query.count()
    return render_template("management/overview.html",
                           python_version=python_version,
                           flask_version=flask_version,
                           flaskbb_version=flaskbb_version,
                           user_count=user_count,
                           topic_count=topic_count,
                           post_count=post_count)


@management.route("/settings", methods=["GET", "POST"])
@management.route("/settings/<path:slug>", methods=["GET", "POST"])
@admin_required
def settings(slug=None):
    slug = slug if slug else "general"

    # get the currently active group
    active_group = SettingsGroup.query.filter_by(key=slug).first_or_404()
    # get all groups - used to build the navigation
    all_groups = SettingsGroup.query.all()

    SettingsForm = Setting.get_form(active_group)

    old_settings = Setting.get_settings(active_group)
    new_settings = {}

    form = SettingsForm()

    if form.validate_on_submit():
        for key, values in iteritems(old_settings):
            try:
                # check if the value has changed
                if values['value'] == form[key].data:
                    continue
                else:
                    new_settings[key] = form[key].data
            except KeyError:
                pass
        Setting.update(settings=new_settings, app=current_app)
        flash(_("Settings saved."), "success")
    else:
        for key, values in iteritems(old_settings):
            try:
                form[key].data = values['value']
            except (KeyError, ValueError):
                pass

    return render_template("management/settings.html", form=form,
                           all_groups=all_groups, active_group=active_group)


# Users
@management.route("/users", methods=['GET', 'POST'])
@moderator_required
def users():
    page = request.args.get("page", 1, type=int)
    search_form = UserSearchForm()

    if search_form.validate():
        users = search_form.get_results().\
            paginate(page, flaskbb_config['USERS_PER_PAGE'], False)
        return render_template("management/users.html", users=users,
                               search_form=search_form)

    users = User.query. \
        order_by(User.id.asc()).\
        paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

    return render_template("management/users.html", users=users,
                           search_form=search_form)


@management.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@moderator_required
def edit_user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()

    if not can_edit_user(current_user):
        flash(_("You are not allowed to edit this user."), "danger")
        return redirect(url_for("management.users"))

    secondary_group_query = Group.query.filter(
        db.not_(Group.id == user.primary_group_id),
        db.not_(Group.banned),
        db.not_(Group.guest == True))

    form = EditUserForm(user)
    form.secondary_groups.query = secondary_group_query
    if form.validate_on_submit():
        form.populate_obj(user)
        user.primary_group_id = form.primary_group.data.id

        # Don't override the password
        if form.password.data:
            user.password = form.password.data

        user.save(groups=form.secondary_groups.data)

        flash(_("User successfully updated."), "success")
        return redirect(url_for("management.edit_user", user_id=user.id))

    return render_template("management/user_form.html", form=form,
                           title=_("Edit User"))


@management.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    user.delete()
    flash(_("User successfully deleted."), "success")
    return redirect(url_for("management.users"))


@management.route("/users/add", methods=["GET", "POST"])
@admin_required
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        form.save()
        flash(_("User successfully added."), "success")
        return redirect(url_for("management.users"))

    return render_template("management/user_form.html", form=form,
                           title=_("Add User"))


@management.route("/users/banned", methods=["GET", "POST"])
@moderator_required
def banned_users():
    page = request.args.get("page", 1, type=int)
    search_form = UserSearchForm()

    users = User.query.filter(
        Group.banned == True,
        Group.id == User.primary_group_id
    ).paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

    if search_form.validate():
        users = search_form.get_results().\
            paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

        return render_template("management/banned_users.html", users=users,
                               search_form=search_form)

    return render_template("management/banned_users.html", users=users,
                           search_form=search_form)


@management.route("/users/<int:user_id>/ban", methods=["POST"])
@moderator_required
def ban_user(user_id):
    if not can_ban_user(current_user):
        flash(_("You do not have the permissions to ban this user."), "danger")
        return redirect(url_for("management.overview"))

    user = User.query.filter_by(id=user_id).first_or_404()

    # Do not allow moderators to ban admins
    if user.get_permissions()['admin'] and \
            (current_user.permissions['mod'] or
             current_user.permissions['super_mod']):

        flash(_("A moderator cannot ban an admin user."), "danger")
        return redirect(url_for("management.overview"))

    if user.ban():
        flash(_("User is now banned."), "success")
    else:
        flash(_("Could not ban user."), "danger")

    return redirect(url_for("management.banned_users"))


@management.route("/users/<int:user_id>/unban", methods=["POST"])
@moderator_required
def unban_user(user_id):
    if not can_ban_user(current_user):
        flash(_("You do not have the permissions to unban this user."),
              "danger")
        return redirect(url_for("management.overview"))

    user = User.query.filter_by(id=user_id).first_or_404()

    if user.unban():
        flash(_("User is now unbanned."), "success")
    else:
        flash(_("Could not unban user."), "danger")

    return redirect(url_for("management.banned_users"))


# Reports
@management.route("/reports")
@moderator_required
def reports():
    page = request.args.get("page", 1, type=int)
    reports = Report.query.\
        order_by(Report.id.asc()).\
        paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

    return render_template("management/reports.html", reports=reports)


@management.route("/reports/unread")
@moderator_required
def unread_reports():
    page = request.args.get("page", 1, type=int)
    reports = Report.query.\
        filter(Report.zapped == None).\
        order_by(Report.id.desc()).\
        paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

    return render_template("management/unread_reports.html", reports=reports)


@management.route("/reports/<int:report_id>/markread", methods=["POST"])
@management.route("/reports/markread", methods=["POST"])
@moderator_required
def report_markread(report_id=None):
    # mark single report as read
    if report_id:

        report = Report.query.filter_by(id=report_id).first_or_404()
        if report.zapped:
            flash(_("Report %(id)s is already marked as read.", id=report.id),
                  "success")
            return redirect(url_for("management.reports"))

        report.zapped_by = current_user.id
        report.zapped = datetime.utcnow()
        report.save()
        flash(_("Report %(id)s marked as read.", id=report.id), "success")
        return redirect(url_for("management.reports"))

    # mark all as read
    reports = Report.query.filter(Report.zapped == None).all()
    report_list = []
    for report in reports:
        report.zapped_by = current_user.id
        report.zapped = datetime.utcnow()
        report_list.append(report)

    db.session.add_all(report_list)
    db.session.commit()

    flash(_("All reports were marked as read."), "success")
    return redirect(url_for("management.reports"))


# Groups
@management.route("/groups")
@admin_required
def groups():
    page = request.args.get("page", 1, type=int)

    groups = Group.query.\
        order_by(Group.id.asc()).\
        paginate(page, flaskbb_config['USERS_PER_PAGE'], False)

    return render_template("management/groups.html", groups=groups)


@management.route("/groups/<int:group_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_group(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()

    form = EditGroupForm(group)

    if form.validate_on_submit():
        form.populate_obj(group)
        group.save()

        if group.guest:
            Guest.invalidate_cache()

        flash(_("Group successfully updated."), "success")
        return redirect(url_for("management.groups", group_id=group.id))

    return render_template("management/group_form.html", form=form,
                           title=_("Edit Group"))


@management.route("/groups/<int:group_id>/delete", methods=["POST"])
@admin_required
def delete_group(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()
    group.delete()
    flash(_("Group successfully deleted."), "success")
    return redirect(url_for("management.groups"))


@management.route("/groups/add", methods=["GET", "POST"])
@admin_required
def add_group():
    form = AddGroupForm()
    if form.validate_on_submit():
        form.save()
        flash(_("Group successfully added."), "success")
        return redirect(url_for("management.groups"))

    return render_template("management/group_form.html", form=form,
                           title=_("Add Group"))


# Forums and Categories
@management.route("/forums")
@admin_required
def forums():
    categories = Category.query.order_by(Category.position.asc()).all()
    return render_template("management/forums.html", categories=categories)


@management.route("/forums/<int:forum_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_forum(forum_id):
    forum = Forum.query.filter_by(id=forum_id).first_or_404()

    form = EditForumForm(forum)
    if form.validate_on_submit():
        form.save()
        flash(_("Forum successfully updated."), "success")
        return redirect(url_for("management.edit_forum", forum_id=forum.id))
    else:
        if forum.moderators:
            form.moderators.data = ",".join([
                user.username for user in forum.moderators
            ])
        else:
            form.moderators.data = None

    return render_template("management/forum_form.html", form=form,
                           title=_("Edit Forum"))


@management.route("/forums/<int:forum_id>/delete", methods=["POST"])
@admin_required
def delete_forum(forum_id):
    forum = Forum.query.filter_by(id=forum_id).first_or_404()

    involved_users = User.query.filter(Topic.forum_id == forum.id,
                                       Post.user_id == User.id).all()

    forum.delete(involved_users)

    flash(_("Forum successfully deleted."), "success")
    return redirect(url_for("management.forums"))


@management.route("/forums/add", methods=["GET", "POST"])
@management.route("/forums/<int:category_id>/add", methods=["GET", "POST"])
@admin_required
def add_forum(category_id=None):
    form = AddForumForm()

    if form.validate_on_submit():
        form.save()
        flash(_("Forum successfully added."), "success")
        return redirect(url_for("management.forums"))
    else:
        # by default all groups have access to a forum
        form.groups.data = Group.query.order_by(Group.name.asc()).all()

        if category_id:
            category = Category.query.filter_by(id=category_id).first()
            form.category.data = category

    return render_template("management/forum_form.html", form=form,
                           title=_("Add Forum"))


@management.route("/category/add", methods=["GET", "POST"])
@admin_required
def add_category():
    form = CategoryForm()

    if form.validate_on_submit():
        form.save()
        flash(_("Category successfully added."), "success")
        return redirect(url_for("management.forums"))

    return render_template("management/category_form.html", form=form,
                           title=_("Add Category"))


@management.route("/category/<int:category_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_category(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()

    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        form.populate_obj(category)
        flash(_("Category successfully updated."), "success")
        category.save()

    return render_template("management/category_form.html", form=form,
                           title=_("Edit Category"))


@management.route("/category/<int:category_id>/delete", methods=["POST"])
@admin_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()

    involved_users = User.query.filter(Forum.category_id == category.id,
                                       Topic.forum_id == Forum.id,
                                       Post.user_id == User.id).all()

    category.delete(involved_users)
    flash(_("Category with all associated forums deleted."), "success")
    return redirect(url_for("management.forums"))


# Plugins
@management.route("/plugins")
@admin_required
def plugins():
    plugins = get_all_plugins()
    return render_template("management/plugins.html", plugins=plugins)


@management.route("/plugins/<path:plugin>/enable", methods=["POST"])
@admin_required
def enable_plugin(plugin):
    plugin = get_plugin_from_all(plugin)
    if not plugin.enabled:
        plugin_dir = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
            "plugins", plugin.identifier
        )

        disabled_file = os.path.join(plugin_dir, "DISABLED")

        try:
            if os.path.exists(disabled_file):
                os.remove(disabled_file)
                flash(_("Plugin is enabled. Please reload your app."), "success")
            else:
                flash(_("Plugin is already enabled. Please reload  your app."), "warning")

        except OSError:
            flash(_("If you are using a host which doesn't support writting on the "
                "disk, this won't work - than you need to delete the "
                "'DISABLED' file by yourself."), "danger")

    else:
        flash(_("Couldn't enable Plugin."), "danger")

    return redirect(url_for("management.plugins"))


@management.route("/plugins/<path:plugin>/disable", methods=["POST"])
@admin_required
def disable_plugin(plugin):
    try:
        plugin = get_plugin(plugin)
    except KeyError:
        flash(_("Plugin %(plugin)s not found.", plugin=plugin.name), "danger")
        return redirect(url_for("management.plugins"))

    plugin_dir = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        "plugins", plugin.identifier
    )

    disabled_file = os.path.join(plugin_dir, "DISABLED")

    try:
        open(disabled_file, "a").close()
        flash(_("Plugin is disabled. Please reload your app."), "success")

    except OSError:
        flash(_("If you are using a host which doesn't "
            "support writting on the disk, this won't work - than you need to "
            "create a 'DISABLED' file by yourself."), "info")

    return redirect(url_for("management.plugins"))


@management.route("/plugins/<path:plugin>/uninstall", methods=["POST"])
@admin_required
def uninstall_plugin(plugin):
    plugin = get_plugin_from_all(plugin)
    if plugin.uninstallable:
        plugin.uninstall()
        Setting.invalidate_cache()

        flash(_("Plugin has been uninstalled."), "success")
    else:
        flash(_("Cannot uninstall Plugin."), "danger")

    return redirect(url_for("management.plugins"))


@management.route("/plugins/<path:plugin>/install", methods=["POST"])
@admin_required
def install_plugin(plugin):
    plugin = get_plugin_from_all(plugin)
    if plugin.installable and not plugin.uninstallable:
        plugin.install()
        Setting.invalidate_cache()

        flash(_("Plugin has been installed."), "success")
    else:
        flash(_("Cannot install Plugin."), "danger")

    return redirect(url_for("management.plugins"))
