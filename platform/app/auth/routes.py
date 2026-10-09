"""Login and logout routes."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user

from .models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            # Generic message: never reveal whether the email exists.
            flash("Invalid email or password.", "error")
            return render_template("login.html"), 401
        login_user(user, remember=False)
        # Prevent open-redirect: only allow relative next URLs.
        next_url = request.args.get("next", "")
        if not next_url.startswith("/") or next_url.startswith("//"):
            next_url = "/"
        return redirect(next_url)
    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))