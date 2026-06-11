import os

from flask import Flask, session

from auth import auth_bp
from comments import comments_bp
from csrf import generate_csrf_token, validate_csrf
from db import init_db
from posts import posts_bp
from reactions import reactions_bp
from search import search_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    if os.environ.get("COOKIE_SECURE") == "1":
        app.config["SESSION_COOKIE_SECURE"] = True

    if test_config:
        app.config.update(test_config)

    if not test_config or not test_config.get("SKIP_INIT_DB"):
        init_db()

    @app.before_request
    def csrf_check():
        from flask import request
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if app.config.get("DISABLE_CSRF"):
                return None
            return validate_csrf()

    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.context_processor
    def inject_globals():
        return {
            "csrf_token": generate_csrf_token(),
            "current_user": session.get("username"),
        }

    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(reactions_bp)
    app.register_blueprint(search_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
