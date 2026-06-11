from flask import Blueprint, jsonify, request, session

from csrf import csrf_protect
from models import create_comment, get_post

comments_bp = Blueprint("comments", __name__)


@comments_bp.route("/api/post/<int:post_id>/comment", methods=["POST"])
@csrf_protect
def add_comment(post_id):
    if "user_id" not in session:
        return jsonify({"ok": False, "error": "Please log in first."}), 401
    post = get_post(post_id)
    if not post:
        return jsonify({"ok": False, "error": "Post not found."}), 404
    body = request.get_json(silent=True)
    if body is None or "body" not in body:
        return jsonify({"ok": False, "error": "Comment cannot be empty."}), 400
    text = body["body"]
    if not isinstance(text, str):
        return jsonify({"ok": False, "error": "Comment must be text."}), 400
    text = text.strip()
    if not text:
        return jsonify({"ok": False, "error": "Comment cannot be empty."}), 400
    if len(text) > 2000:
        return jsonify({"ok": False, "error": "Comment must be at most 2000 characters."}), 400
    comment = create_comment(post_id, session["user_id"], text)
    return jsonify({"ok": True, "comment": comment}), 201
