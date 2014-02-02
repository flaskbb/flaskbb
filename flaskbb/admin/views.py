# -*- coding: utf-8 -*-
"""
    flaskbb.admin.views
    ~~~~~~~~~~~~~~~~~~~

    This module handles the admin views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import sys

from flask import (Blueprint, render_template, current_app, request, redirect,
                   url_for, flash, __version__ as flask_version)

from flaskbb import __version__ as flaskbb_version
from flaskbb.utils.decorators import admin_required
from flaskbb.extensions import db
from flaskbb.user.models import User, Group
from flaskbb.forum.models import Post, Topic, Forum, Category
from flaskbb.admin.forms import (AddUserForm, EditUserForm, AddGroupForm,
                                 EditGroupForm, ForumForm, CategoryForm)


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


@admin.route("/users")
@admin_required
def users():
    page = request.args.get("page", 1, type=int)

    users = User.query.\
        paginate(page, current_app.config['USERS_PER_PAGE'], False)

    return render_template("admin/users.html", users=users)


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
        user.username = form.username.data
        user.email = form.email.data
        user.birthday = form.birthday.data
        user.gender = form.gender.data
        user.website = form.website.data
        user.location = form.location.data
        user.signature = form.signature.data
        user.avatar = form.avatar.data
        user.notes = form.notes.data
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

    form = ForumForm()
    form._id = forum.id  # Used for validation only.

    if form.validate_on_submit():
        forum.title = form.title.data
        forum.description = form.description.data
        forum.position = form.position.data
        forum.locked = form.locked.data
        forum.category_id = form.category.data.id

        if form.moderators.data:
            forum.moderators = form.moderators.data

        forum.save()

        flash("Forum successfully edited.", "success")
        return redirect(url_for("admin.edit_forum", forum_id=forum.id))
    else:
        form.title.data = forum.title
        form.description.data = forum.description
        form.position.data = forum.position
        form.category.data = forum.category
        form.locked.data = forum.locked

        if forum.moderators:
            mods = User.query.filter(User.id.in_(forum.moderators)).all()
            form.moderators.data = ",".join([mod.username for mod in mods])
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
    form = ForumForm()

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
def add_category():
    form = CategoryForm()

    if form.validate_on_submit():
        form.save()
        flash("Category successfully created.", "success")
        return redirect(url_for("admin.forums"))

    return render_template("admin/category_form.html", form=form,
                           title="Add Category")


@admin.route("/category/<int:category_id>/edit", methods=["GET", "POST"])
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
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first_or_404()

    involved_users = User.query.filter(Forum.category_id == category.id,
                                       Topic.forum_id == Forum.id,
                                       Post.user_id == User.id).all()

    category.delete(involved_users)
    flash("Category with all associated forums deleted.", "success")
    return redirect(url_for("admin.forums"))
