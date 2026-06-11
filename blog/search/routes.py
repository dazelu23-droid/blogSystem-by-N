from flask import Blueprint, render_template, request

from csrf import generate_csrf_token
from models import list_posts, truncate_preview

search_bp = Blueprint("search", __name__)


@search_bp.route("/search")
def search():
    q = (request.args.get("q") or "").strip()[:100]
    if not q:
        return render_template(
            "search.html", query="", posts=[], prompt=True,
            csrf_token=generate_csrf_token()
        )
    posts = list_posts(search=q)
    for p in posts:
        p["preview"] = truncate_preview(p["body"])
    return render_template(
        "search.html", query=q, posts=posts, prompt=False,
        csrf_token=generate_csrf_token()
    )
