"""Authentication blueprint, decorators, and session helpers."""
from __future__ import annotations

import datetime as dt
from functools import wraps
from typing import Callable

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from models import db, User
from models.user import VALID_ROLES

auth_bp = Blueprint("auth", __name__, url_prefix="")

ROLE_DASHBOARD = {
    "admin": "admin.admin_dashboard",
    "doctor": "doctor.doctor_dashboard",
    "patient": "patient.patient_dashboard",
}

ALLOWED_POST_LOGIN = {
    "admin": "/admin/dashboard",
    "doctor": "/doctor/dashboard",
    "patient": "/patient/dashboard",
}

# Trusted post-login redirect targets besides the primary dashboard URL.
ALLOWED_POST_LOGIN_EXTRAS: dict[str, frozenset[str]] = {
    "patient": frozenset({"/diagnosis"}),
}


def current_user() -> User | None:
    uid = session.get("user_id")
    if not uid:
        return None
    return db.session.get(User, uid)


def _safe_redirect_path(path: str | None, user: User) -> str | None:
    if not path or path.startswith("//"):
        return None
    norm = "/" + path.strip().lstrip("/")
    norm = norm.rstrip("/") or "/"
    allowed = ALLOWED_POST_LOGIN.get(user.role)
    if not allowed:
        return None
    allow_norm = allowed.rstrip("/") or "/"
    if norm == allow_norm:
        return allowed
    extras = ALLOWED_POST_LOGIN_EXTRAS.get(user.role)
    if extras and norm in extras:
        return norm
    return None


def role_required(*allowed_roles: str) -> Callable:
    roles = set(allowed_roles)

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                return redirect(url_for("auth.login", next=request.path))
            if user.role not in roles:
                flash("You do not have access to this area.", "danger")
                ep = ROLE_DASHBOARD.get(user.role, "auth.login")
                return redirect(url_for(ep))
            return view(*args, **kwargs)

        return wrapped

    return decorator


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    user = current_user()
    if user is not None:
        return redirect(url_for(ROLE_DASHBOARD[user.role]))

    portal_default = request.args.get("portal", "patient")
    if portal_default not in VALID_ROLES:
        portal_default = "patient"

    next_arg = request.args.get("next")

    if request.method == "POST":
        portal = request.form.get("portal", "patient").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"
        next_form = request.form.get("next", "").strip() or None

        if portal not in VALID_ROLES:
            portal = "patient"

        acct = User.query.filter_by(email=email).first()
        if acct is None or not check_password_hash(acct.password, password):
            flash("Invalid email or password.", "danger")
            return render_template(
                "login.html",
                portal=portal,
                next_url=next_form or next_arg,
                email_value=email,
            )

        if acct.role != portal:
            flash(
                "This credential belongs to a different portal. Switch the Patient / Doctor / Admin tab.",
                "warning",
            )
            return render_template(
                "login.html",
                portal=acct.role,
                next_url=next_form or next_arg,
                email_value=email,
            )

        session.clear()
        session.permanent = remember
        session["user_id"] = acct.id

        trusted = _safe_redirect_path(next_form or next_arg, acct)
        if trusted:
            return redirect(trusted)

        return redirect(url_for(ROLE_DASHBOARD[acct.role]))

    next_url = next_arg if next_arg else None
    return render_template(
        "login.html",
        portal=portal_default,
        next_url=next_url,
        email_value="",
    )


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    user = current_user()
    if user is not None:
        return redirect(url_for(ROLE_DASHBOARD[user.role]))

    # Create account is for patients only; doctors and admins are added by administrators.
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        has_error = False
        dob_val: dt.date | None = None
        dob_raw = (request.form.get("date_of_birth") or "").strip()
        if dob_raw:
            try:
                dob_val = dt.datetime.strptime(dob_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Date of birth must be YYYY-MM-DD.", "danger")
                has_error = True

        if len(name) < 2:
            flash("Enter your full name (at least 2 characters).", "danger")
            has_error = True
        parts = email.split("@")
        if len(parts) != 2 or len(parts[0].strip()) < 1 or len(parts[1].strip()) < 1:
            flash("Please enter a valid email address.", "danger")
            has_error = True
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            has_error = True
        elif password != confirm:
            flash("Passwords do not match.", "danger")
            has_error = True

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            has_error = True

        if has_error:
            return render_template(
                "register.html",
                form_name=name,
                form_email=email,
                form_dob=dob_raw,
            )

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role="patient",
            department=None,
            date_of_birth=dob_val,
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully. Sign in to continue.", "success")
        return redirect(url_for("auth.login", portal="patient"))

    return render_template(
        "register.html",
        form_name="",
        form_email="",
        form_dob="",
    )


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password")
def forgot_password():
    """Password reset flows are orchestrated offline; this page routes users to admins."""
    return render_template("forgot_password.html")
