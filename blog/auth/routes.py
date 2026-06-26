from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from auth.email import send_password_reset_email
from auth.utils import safe_next_url, validate_password, validate_signup
from csrf import csrf_protect, generate_csrf_token
from db import get_db
from models import (
    create_password_reset_token,
    create_user,
    get_user_by_email,
    get_user_by_username,
    get_user_id_for_reset_token,
    update_user_password,
)
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", csrf_token=generate_csrf_token(), errors=[])
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip()
    password = request.form.get("password") or ""
    errors = validate_signup(username, email, password)
    if errors:
        return render_template(
            "signup.html", csrf_token=generate_csrf_token(), errors=errors,
            username=username, email=email
        ), 400
    try:
        password_hash = generate_password_hash(password)
        create_user(username, email, password_hash)
    except Exception:
        errors = ["That username is already taken."]
        conn = get_db()
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email.lower(),)).fetchone()
        conn.close()
        if row:
            errors = ["That email is already registered."]
        return render_template(
            "signup.html", csrf_token=generate_csrf_token(), errors=errors,
            username=username, email=email
        ), 400
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or request.form.get("next") or "/"
    if request.method == "GET":
        return render_template(
            "login.html", csrf_token=generate_csrf_token(), next=next_url, error=None
        )
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    user = get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return render_template(
            "login.html", csrf_token=generate_csrf_token(), next=next_url,
            error="Invalid username or password."
        ), 400
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    generate_csrf_token()
    return redirect(safe_next_url(next_url))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template(
            "forgot_password.html",
            csrf_token=generate_csrf_token(),
            errors=[],
            message=None,
            dev_reset_url=None,
        )
    email = (request.form.get("email") or "").strip()
    if not email:
        return render_template(
            "forgot_password.html",
            csrf_token=generate_csrf_token(),
            errors=["Please enter your email address."],
            message=None,
            dev_reset_url=None,
            email=email,
        ), 400

    message = (
        "If that email is registered, we sent a link to reset your password. "
        "Check your inbox."
    )
    dev_reset_url = None
    user = get_user_by_email(email)
    if user:
        token = create_password_reset_token(user["id"])
        reset_url = url_for("auth.reset_password", token=token, _external=True)
        sent = send_password_reset_email(user["email"], reset_url, current_app)
        if current_app.config.get("TESTING") and not sent:
            dev_reset_url = url_for("auth.reset_password", token=token)

    return render_template(
        "forgot_password.html",
        csrf_token=generate_csrf_token(),
        errors=[],
        message=message,
        dev_reset_url=dev_reset_url,
    )


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user_id = get_user_id_for_reset_token(token)
    if not user_id:
        return render_template(
            "reset_password.html",
            csrf_token=generate_csrf_token(),
            token=token,
            error="This reset link is invalid or has expired.",
            errors=[],
        ), 400

    if request.method == "GET":
        return render_template(
            "reset_password.html",
            csrf_token=generate_csrf_token(),
            token=token,
            error=None,
            errors=[],
        )

    password = request.form.get("password") or ""
    password_confirm = request.form.get("password_confirm") or ""
    errors = validate_password(password)
    if password != password_confirm:
        errors.append("Passwords do not match.")
    if errors:
        return render_template(
            "reset_password.html",
            csrf_token=generate_csrf_token(),
            token=token,
            error=None,
            errors=errors,
        ), 400

    update_user_password(user_id, generate_password_hash(password))
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout", methods=["POST"])
@csrf_protect
def logout():
    session.clear()
    return redirect(url_for("posts.index"))
