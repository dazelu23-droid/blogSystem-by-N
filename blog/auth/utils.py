import re
from functools import wraps

from flask import abort, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db
from models import create_user, get_user_by_username

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated


def author_required(get_post_id):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login", next=request.path))
            post_id = kwargs.get(get_post_id) or (args[0] if args else None)
            from models import get_post
            post = get_post(post_id)
            if not post:
                abort(404)
            if post["author_id"] != session["user_id"]:
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator


def safe_next_url(next_url):
    if not next_url:
        return "/"
    if not next_url.startswith("/"):
        return "/"
    if next_url.startswith("//"):
        return "/"
    if "\\" in next_url:
        return "/"
    return next_url


def validate_signup(username, email, password):
    errors = []
    if not USERNAME_RE.match(username or ""):
        errors.append("Username must be 3-30 letters, digits, or underscores.")
    elif get_user_by_username(username):
        errors.append("That username is already taken.")
    if not EMAIL_RE.match(email or ""):
        errors.append("Please enter a valid email address.")
    else:
        conn = get_db()
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email.lower(),)).fetchone()
        conn.close()
        if row:
            errors.append("That email is already registered.")
    if not password or len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    return errors
