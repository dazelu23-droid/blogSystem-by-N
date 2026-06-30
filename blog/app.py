import os

from flask import Flask, redirect, send_from_directory, session

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
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; img-src 'self' data: https://images.unsplash.com"
        )
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

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    @app.get("/workout")
    def workout_short():
        return redirect("/workout-blog.html")

    @app.get("/workout-blog.html")
    def workout_blog():
        return send_from_directory(project_root, "workout-blog.html")

    workouts_dir = os.path.join(project_root, "blog-workers", "public", "workouts")

    @app.get("/workouts/<path:filename>")
    def workout_guide_page(filename):
        if filename not in ("strength.html", "cardio.html", "hiit.html", "flexibility.html"):
            from flask import abort
            abort(404)
        return send_from_directory(workouts_dir, filename)

    return app


if __name__ == "__main__":
    app = create_app()
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
