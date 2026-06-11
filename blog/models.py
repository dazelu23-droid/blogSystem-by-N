import re
from db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(username, email, password_hash):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email.lower(), password_hash),
        )
        conn.commit()
        user_id = cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return user_id


def create_post(author_id, title, body):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO posts (author_id, title, body) VALUES (?, ?, ?)",
        (author_id, title, body),
    )
    conn.commit()
    post_id = cur.lastrowid
    conn.close()
    return post_id


def get_post(post_id):
    conn = get_db()
    row = conn.execute(
        """
        SELECT p.*, u.username AS author
        FROM posts p JOIN users u ON p.author_id = u.id
        WHERE p.id = ?
        """,
        (post_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_post(post_id, title, body):
    conn = get_db()
    conn.execute(
        "UPDATE posts SET title = ?, body = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (title, body, post_id),
    )
    conn.commit()
    conn.close()


def delete_post(post_id):
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()


def list_posts(limit=None, search=None):
    conn = get_db()
    if search:
        pattern = _escape_like(search)
        rows = conn.execute(
            """
            SELECT p.*, u.username AS author
            FROM posts p JOIN users u ON p.author_id = u.id
            WHERE p.title LIKE ? ESCAPE '\\' OR p.body LIKE ? ESCAPE '\\'
            ORDER BY p.created_at DESC, p.id DESC
            """,
            (f"%{pattern}%", f"%{pattern}%"),
        ).fetchall()
    else:
        query = """
            SELECT p.*, u.username AS author
            FROM posts p JOIN users u ON p.author_id = u.id
            ORDER BY p.created_at DESC, p.id DESC
        """
        if limit:
            query += f" LIMIT {int(limit)}"
        rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _escape_like(s):
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def truncate_preview(text, length=150):
    words = text.split()
    result = []
    total = 0
    for word in words:
        if total + len(word) + (1 if result else 0) > length:
            break
        if result:
            total += 1
        total += len(word)
        result.append(word)
    preview = " ".join(result)
    if preview != text.strip():
        preview += "..."
    return preview


def get_comments(post_id):
    conn = get_db()
    rows = conn.execute(
        """
        SELECT c.*, u.username AS author
        FROM comments c JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC, c.id ASC
        """,
        (post_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_comment(post_id, user_id, body):
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO comments (post_id, user_id, body) VALUES (?, ?, ?)",
        (post_id, user_id, body),
    )
    conn.commit()
    comment_id = cur.lastrowid
    row = conn.execute(
        """
        SELECT c.*, u.username AS author
        FROM comments c JOIN users u ON c.user_id = u.id
        WHERE c.id = ?
        """,
        (comment_id,),
    ).fetchone()
    conn.close()
    return dict(row)


def get_reaction_counts(post_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT kind, COUNT(*) AS cnt FROM reactions WHERE post_id = ? GROUP BY kind",
        (post_id,),
    ).fetchall()
    conn.close()
    counts = {"like": 0, "dislike": 0}
    for row in rows:
        counts[row["kind"]] = row["cnt"]
    return counts


def get_user_reaction(post_id, user_id):
    if not user_id:
        return None
    conn = get_db()
    row = conn.execute(
        "SELECT kind FROM reactions WHERE post_id = ? AND user_id = ?",
        (post_id, user_id),
    ).fetchone()
    conn.close()
    return row["kind"] if row else None


def set_reaction(post_id, user_id, kind):
    conn = get_db()
    existing = conn.execute(
        "SELECT id, kind FROM reactions WHERE post_id = ? AND user_id = ?",
        (post_id, user_id),
    ).fetchone()

    result_kind = kind
    if existing:
        if existing["kind"] == kind:
            conn.execute("DELETE FROM reactions WHERE id = ?", (existing["id"],))
            result_kind = None
        else:
            conn.execute(
                "UPDATE reactions SET kind = ? WHERE id = ?", (kind, existing["id"])
            )
    else:
        conn.execute(
            "INSERT INTO reactions (post_id, user_id, kind) VALUES (?, ?, ?)",
            (post_id, user_id, kind),
        )
    conn.commit()
    conn.close()
    return result_kind
