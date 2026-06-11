from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from auth.utils import safe_next_url, validate_signup
from csrf import csrf_protect, generate_csrf_token
from db import get_db
from models import create_user, get_user_by_username
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


@auth_bp.route("/logout", methods=["POST"])
@csrf_protect
def logout():
    session.clear()
    return redirect(url_for("posts.index"))
