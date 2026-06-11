import secrets
from functools import wraps

from flask import jsonify, request, session


def generate_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def validate_csrf():
    token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    expected = session.get("csrf_token")
    if not token or not expected or not secrets.compare_digest(token, expected):
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": "Invalid or missing CSRF token."}), 400
        return "Invalid or missing CSRF token.", 400
    return None


def csrf_protect(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            error = validate_csrf()
            if error:
                return error
        return f(*args, **kwargs)
    return decorated
