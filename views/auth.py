"""Login / logout — the front door for the app.

Authenticates against the same USERS list the Admin page manages (see
views/admin.py): add a user there with a username/password/role and they
can sign in here with those exact credentials. On success the session
carries the user's id, name, and role, which is what every other page's
role checks (is_manager_or_admin, Staff-only task scoping, etc.) read.
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from data import USERS

auth_bp = Blueprint("auth", __name__)


def _find_user(username, password):
    username = (username or "").strip().lower()
    for u in USERS:
        if u["username"].lower() == username and u["password"] == password:
            return u
    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = _find_user(request.form.get("username", ""), request.form.get("password", ""))
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["staff_name"] = user["name"]
            flash(f"Welcome back, {user['name']}")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard.dashboard"))
        flash("Incorrect username or password")
    return render_template("login.html")


@auth_bp.post("/logout")
def logout():
    session.clear()
    flash("Signed out")
    return redirect(url_for("auth.login"))
