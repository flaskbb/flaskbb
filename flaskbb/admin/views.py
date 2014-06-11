# -*- coding: utf-8 -*-
"""
    flaskbb.admin.views
    ~~~~~~~~~~~~~~~~~~~

    This module handles the admin views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys
import os
from datetime import datetime

from flask import (Blueprint, current_app, request, redirect, url_for, flash,
                   __version__ as flask_version)
from flask.ext.login import current_user
from flask.ext.plugins import get_all_plugins, get_plugin, get_plugin_from_all

from flaskbb import __version__ as flaskbb_version
from flaskbb.forum.forms import UserSearchForm
from flaskbb.utils.helpers import render_template
from flaskbb.utils.decorators import admin_required
from flaskbb.extensions import db
from flaskbb.user.models import User, Group
from flaskbb.forum.models import Post, Topic, Forum, Category, Report
from flaskbb.admin.models import Setting, SettingsGroup
from flaskbb.admin.forms import (AddUserForm, EditUserForm, AddGroupForm,
                                 EditGroupForm, EditForumForm, AddForumForm,
                                 CategoryForm)


admin = Blueprint("admin", __name__)


@admin.route("/")
@admin_required
def overview():
    python_version = "%s.%s" % (sys.version_info[0], sys.version_info[1])
    user_count = User.query.count()
    topic_count = Topic.query.count()
    post_count = Post.query.count()
    return render_template("admin/overview.html",
                           python_version=python_version,
                           flask_version=flask_version,
                           flaskbb_version=flaskbb_version,
                           user_count=user_count,
                           topic_count=topic_count,
                           post_count=post_count)


@admin.route("/settings", methods=["GET", "POST"])
@admin.route("/settings/<path:slug>", methods=["GET", "POST"])
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
        for key, values in old_settings.iteritems():
            try:
                # check if the value has changed
                if values['value'] == form[key].data:
                    continue
                else:
                    new_settings[key] = form[key].data
            except KeyError:
                pass

        Setting.update(settings=new_settings, app=current_app)
    else:
        for key, values in old_settings.iteritems():
            try:
                form[key].data = values['value']
            except (KeyError, ValueError):
                pass

    return render_template("admin/settings.html", form=form,
                           all_groups=all_groups, active_group=active_group)


@admin.route("/users", methods=['GET', 'POST'])
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    search_form = UserSearchForm()

    if search_form.validate():
        users = search_form.get_results().\
            paginate(page, current_app.config['USERS_PER_PAGE'], False)
        return render_template("admin/users.html", users=users,
                               search_form=search_form)

    users = User.query. \
        paginate(page, current_app.config['USERS_PER_PAGE'], False)

    return render_template("admin/users.html", users=users,
                           search_form=search_form)


@admin.route("/groups")
@admin_required
def groups():
    page = request.args.get("page", 1, type=int)

    groups = Group.query.\
        paginate(page, current_app.config['USERS_PER_PAGE'], False)

    return render_template("admin/groups.html", groups=groups)


@admin.route("/forums")
@admin_required
def forums():
    categories = Category.query.order_by(Category.position.asc()).all()
    return render_template("admin/forums.html", categories=categories)


@admin.route("/reports")
@admin_required
def reports():
    page = request.args.get("page", 1, type=int)
    reports = Report.query.\
        order_by(Report.id.asc()).\
        paginate(page, current_app.config['USERS_PER_PAGE'], False)

    return render_template("admin/reports.html", reports=reports)


@admin.route("/plugins")
@admin_required
def plugins():
    plugins = get_all_plugins()
    return render_template("admin/plugins.html", plugins=plugins)


@admin.route("/plugins/enable/<plugin>")
def enable_plugin(plugin):
    plugin = get_plugin_from_all(plugin)
    if not plugin.enabled:
        plugin_dir = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
            "plugins", plugin.identifier
        )

        disabled_file = os.path.join(plugin_dir, "DISABLED")

        os.remove(disabled_file)

        flash("Plugin should be enabled. Please reload your app.", "success")

        flash("If you are using a host which doesn't support writting on the "
              "disk, this won't work - than you need to delete the "
              "'DISABLED' file by yourself.", "info")
    else:
        flash("Plugin is not enabled", "danger")

    return redirect(url_for("admin.plugins"))


@admin.route("/plugins/disable/<plugin>")
def disable_plugin(plugin):
    try:
        plugin = get_plugin(plugin)
    except KeyError:
        flash("Plugin {} not found".format(plugin), "danger")
        return redirect(url_for("admin.plugins"))

    plugin_dir = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        "plugins", plugin.identifier
    )

    disabled_file = os.path.join(plugin_dir, "DISABLED")

    open(disabled_file, "a").close()

    flash("Plugin should be disabled. Please reload your app.", "success")

    flash("If you are using a host which doesn't "
          "support writting on the disk, this won't work - than you need to "
          "create a 'DISABLED' file by yourself.", "info")

    return redirect(url_for("admin.plugins"))


@admin.route("/plugins/uninstall/<plugin>")
def uninstall_plugin(plugin):
    plugin = get_plugin_from_all(plugin)
    if plugin.uninstallable:
        plugin.uninstall()
        flash("Plugin {} has been uninstalled.".format(plugin.name), "success")
    else:
        flash("Cannot uninstall Plugin {}".format(plugin.name), "danger")

    return redirect(url_for("admin.plugins"))


@admin.route("/plugins/install/<plugin>")
def install_plugin(plugin):
    plugin = get_plugin_from_all(plugin)
    if plugin.installable and not plugin.uninstallable:
        plugin.install()
        flash("Plugin {} has been installed.".format(plugin.name), "success")
    else:
        flash("Cannot install Plugin {}".format(plugin.name), "danger")

    return redirect(url_for("admin.plugins"))


@admin.route("/reports/unread")
@admin_required
def unread_reports():
    page = request.args.get("page", 1, type=int)
    reports = Report.query.\
        filter(Report.zapped == None).\
        order_by(Report.id.desc()).\
        paginate(page, current_app.config['USERS_PER_PAGE'], False)

    return render_template("admin/unread_reports.html", reports=reports)


@admin.route("/reports/<int:report_id>/markread")
@admin.route("/reports/markread")
@admin_required
def report_markread(report_id=None):
    # mark single report as read
    if report_id:

        report = Report.query.filter_by(id=report_id).first_or_404()
        if report.zapped:
            flash("Report %s is already marked as read" % report.id, "success")
            return redirect(url_for("admin.reports"))

        report.zapped_by = current_user.id
        report.zapped = datetime.utcnow()
        report.save()
        flash("Report %s marked as read" % report.id, "success")
        return redirect(url_for("admin.reports"))

    # mark all as read
    reports = Report.query.filter(Report.zapped == None).all()
    report_list = []
    for report in reports:
        report.zapped_by = current_user.id
        report.zapped = datetime.utcnow()
        report_list.append(report)

    db.session.add_all(report_list)
    db.session.commit()

    flash("All reports were marked as read", "success")
    return redirect(url_for("admin.reports"))


@admin.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()

    secondary_group_query = Group.query.filter(
        db.not_(Group.id == user.primary_group_id),
        db.not_(Group.banned == True),
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

        flash("User successfully edited", "success")
        return redirect(url_for("admin.edit_user", user_id=user.id))
    else:
        form.username.data = user.username
        form.email.data = user.email
        form.birthday.data = user.birthday
        form.gender.data = user.gender
        form.website.data = user.website
        form.location.data = user.location
        form.signature.data = user.signature
        form.avatar.data = user.avatar
        form.notes.data = user.notes
        form.primary_group.data = user.primary_group
        form.secondary_groups.data = user.secondary_groups

    return render_template("admin/user_form.html", form=form,
                           title="Edit User")


@admin.route("/users/<int:user_id>/delete")
@admin_required
def delete_user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    user.delete()
    flash("User successfully deleted", "success")
    return redirect(url_for("admin.users"))


@admin.route("/users/add", methods=["GET", "POST"])
@admin_required
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        form.save()
        flash("User successfully added.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/user_form.html", form=form,
                           title="Add User")


@admin.route("/groups/<int:group_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_group(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()

    form = EditGroupForm(group)
    if form.validate_on_submit():
        form.populate_obj(group)
        group.save()

        flash("Group successfully edited.", "success")
        return redirect(url_for("admin.groups", group_id=group.id))
    else:
        form.name.data = group.name
        form.description.data = group.description
        form.admin.data = group.admin
        form.super_mod.data = group.super_mod
        form.mod.data = group.mod
        form.guest.data = group.guest
        form.banned.data = group.banned
        form.editpost.data = group.editpost
        form.deletepost.data = group.deletepost
        form.deletetopic.data = group.deletetopic
        form.posttopic.data = group.posttopic
        form.postreply.data = group.postreply

    return render_template("admin/group_form.html", form=form,
                           title="Edit Group")


@admin.route("/groups/<int:group_id>/delete")
@admin_required
def delete_group(group_id):
    group = Group.query.filter_by(id=group_id).first_or_404()
    group.delete()
    flash("Group successfully deleted.", "success")
    return redirect(url_for("admin.groups"))


@admin.route("/groups/add", methods=["GET", "POST"])
@admin_required
def add_group():
    form = AddGroupForm()
    if form.validate_on_submit():
        form.save()
        flash("Group successfully added.", "success")
        return redirect(url_for("admin.groups"))

    return render_template("admin/group_form.html", form=form,
                           title="Add Group")


@admin.route("/forums/<int:forum_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_forum(forum_id):
    forum = Forum.query.filter_by(id=forum_id).first_or_404()

    form = EditForumForm(forum)
    if form.validate_on_submit():
        form.populate_obj(forum)
        forum.save(moderators=form.moderators.data)

        flash("Forum successfully edited.", "success")
        return redirect(url_for("admin.edit_forum", forum_id=forum.id))
    else:
        form.title.data = forum.title
        form.description.data = forum.description
        form.position.data = forum.position
        form.category.data = forum.category
        form.external.data = forum.external
        form.locked.data = forum.locked
        form.show_moderators.data = forum.show_moderators

        if forum.moderators:
            form.moderators.data = ",".join([user.username
                                            for user in forum.moderators])
        else:
            form.moderators.data = None

    return render_template("admin/forum_form.html", form=form,
                           title="Edit Forum")


@admin.route("/forums/<int:forum_id>/delete")
@admin_required
def delete_forum(forum_id):
    forum = Forum.query.filter_by(id=forum_id).first_or_404()

    involved_users = User.query.filter(Topic.forum_id == forum.id,
                                       Post.user_id == User.id).all()

    forum.delete(involved_users)

    flash("Forum successfully deleted.", "success")
    return redirect(url_for("admin.forums"))


@admin.route("/forums/add", methods=["GET", "POST"])
@admin.route("/forums/<int:category_id>/add", methods=["GET", "POST"])
@admin_required
def add_forum(category_id=None):
    form = AddForumForm()

    if form.validate_on_submit():
        form.save()
        flash("Forum successfully added.", "success")
        return redirect(url_for("admin.forums"))
    else:
        if category_id:
            category = Category.query.filter_by(id=category_id).first()
            form.category.data = category

    return render_template("admin/forum_form.html", form=form,
                           title="Add Forum")


@admin.route("/category/add", methods=["GET", "POST"])
@admin_required
def add_category():
    form = CategoryForm()

    if form.validate_on_submit():
        form.save()
        flash("Category successfully created.", "success")
        return redirect(url_for("admin.forums"))

    return render_template("admin/category_form.html", form=form,
                           title="Add Category")


@admin.route("/category/<int:category_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_category(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()

    form = CategoryForm()

    if form.validate_on_submit():
        form.populate_obj(category)
        category.save()
    else:
        form.title.data = category.title
        form.description.data = category.description
        form.position.data = category.position

    return render_template("admin/category_form.html", form=form,
                           title="Edit Category")


@admin.route("/category/<int:category_id>/delete", methods=["GET", "POST"])
@admin_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()

    involved_users = User.query.filter(Forum.category_id == category.id,
                                       Topic.forum_id == Forum.id,
                                       Post.user_id == User.id).all()

    category.delete(involved_users)
    flash("Category with all associated forums deleted.", "success")
    return redirect(url_for("admin.forums"))
