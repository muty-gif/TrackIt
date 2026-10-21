"""Page routes.

These serve the HTML shells only; all data is loaded by the browser through the
JSON API. They still enforce the page-level authentication guard so an
unauthenticated visitor is redirected to the login page.
"""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for

from ..auth.utils import get_current_user

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    if get_current_user():
        return render_template("dashboard.html")
    return redirect(url_for("main.login_page"))


@main_bp.get("/dashboard")
def dashboard_page():
    if not get_current_user():
        return redirect(url_for("main.login_page", next=request.path))
    return redirect(url_for("main.index"))


@main_bp.get("/login")
def login_page():
    if get_current_user():
        return redirect(url_for("main.index"))
    return render_template("login.html")


@main_bp.get("/register")
def register_page():
    if get_current_user():
        return redirect(url_for("main.index"))
    return render_template("register.html")


@main_bp.get("/projects")
def projects_page():
    if not get_current_user():
        return redirect(url_for("main.login_page", next=request.path))
    return render_template("projects.html")


@main_bp.get("/projects/<int:project_id>")
def project_page(project_id: int):
    if not get_current_user():
        return redirect(url_for("main.login_page", next=request.path))
    return render_template("project.html")
