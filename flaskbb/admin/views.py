# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, current_app, request
from flaskbb.decorators import admin_required
from flaskbb.user.models import User, Group
from flaskbb.forum.models import Forum, Category


admin = Blueprint("admin", __name__)

@admin.route("/")
@admin_required
def overview():
    return render_template("admin/overview.html")


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


@admin.route("/categories")
@admin_required
def categories():
    page = request.args.get("page", 1, type=int)
    categories = Category.query.\
        paginate(page, current_app.config['USERS_PER_PAGE'], False)
    return render_template("admin/categories.html", categories=categories)


@admin.route("/forums")
@admin_required
def forums():
    page = request.args.get("page", 1, type=int)
    forums = Forum.query.\
        paginate(page, current_app.config['USERS_PER_PAGE'], False)
    return render_template("admin/forums.html", forums=forums)
