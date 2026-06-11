from flask import Blueprint, jsonify, request, session

from csrf import csrf_protect
from models import get_post, get_reaction_counts, set_reaction

reactions_bp = Blueprint("reactions", __name__)


@reactions_bp.route("/api/post/<int:post_id>/react", methods=["POST"])
@csrf_protect
def react(post_id):
    if "user_id" not in session:
        return jsonify({"ok": False, "error": "Please log in first."}), 401
    post = get_post(post_id)
    if not post:
        return jsonify({"ok": False, "error": "Post not found."}), 404
    data = request.get_json(silent=True) or {}
    kind = data.get("kind")
    if kind not in ("like", "dislike"):
        return jsonify({"ok": False, "error": "Reaction must be 'like' or 'dislike'."}), 400
    result = set_reaction(post_id, session["user_id"], kind)
    counts = get_reaction_counts(post_id)
    return jsonify({"ok": True, "reaction": result, "counts": counts})
