from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from auth.utils import author_required, login_required
from csrf import csrf_protect, generate_csrf_token
from models import (
    create_post,
    delete_post,
    get_post,
    list_posts,
    truncate_preview,
    update_post,
)

posts_bp = Blueprint("posts", __name__)


def validate_post(title, body):
    errors = []
    title = (title or "").strip()
    body = (body or "").strip()
    if not title:
        errors.append("Title cannot be empty.")
    elif len(title) > 200:
        errors.append("Title must be at most 200 characters.")
    if not body:
        errors.append("Body cannot be empty.")
    elif len(body) > 20000:
        errors.append("Body must be at most 20000 characters.")
    return errors, title, body


@posts_bp.route("/")
def index():
    posts = list_posts()
    for p in posts:
        p["preview"] = truncate_preview(p["body"])
    return render_template("index.html", posts=posts, csrf_token=generate_csrf_token())


@posts_bp.route("/post/<int:post_id>")
def detail(post_id):
    post = get_post(post_id)
    if not post:
        abort(404)
    from models import get_comments, get_reaction_counts, get_user_reaction
    comments = get_comments(post_id)
    counts = get_reaction_counts(post_id)
    user_reaction = get_user_reaction(post_id, session.get("user_id"))
    return render_template(
        "post.html", post=post, comments=comments, counts=counts,
        user_reaction=user_reaction, csrf_token=generate_csrf_token()
    )


@posts_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "GET":
        return render_template("edit.html", post=None, csrf_token=generate_csrf_token(), errors=[])
    errors, title, body = validate_post(request.form.get("title"), request.form.get("body"))
    if errors:
        return render_template(
            "edit.html", post={"title": title, "body": body},
            csrf_token=generate_csrf_token(), errors=errors
        ), 400
    post_id = create_post(session["user_id"], title, body)
    return redirect(url_for("posts.detail", post_id=post_id))


@posts_bp.route("/edit/<int:post_id>", methods=["GET", "POST"])
@author_required("post_id")
def edit_post(post_id):
    post = get_post(post_id)
    if request.method == "GET":
        return render_template("edit.html", post=post, csrf_token=generate_csrf_token(), errors=[])
    errors, title, body = validate_post(request.form.get("title"), request.form.get("body"))
    if errors:
        return render_template(
            "edit.html", post={"id": post_id, "title": title, "body": body},
            csrf_token=generate_csrf_token(), errors=errors
        ), 400
    update_post(post_id, title, body)
    return redirect(url_for("posts.detail", post_id=post_id))


@posts_bp.route("/delete/<int:post_id>", methods=["POST"])
@csrf_protect
@author_required("post_id")
def delete_post_route(post_id):
    delete_post(post_id)
    return redirect(url_for("posts.index"))
