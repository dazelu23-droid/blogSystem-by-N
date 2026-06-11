import { Hono } from "hono";
import { getCookie, setCookie, deleteCookie } from "hono/cookie";
import { html, raw } from "hono/html";

const app = new Hono();

const USERNAME_RE = /^[A-Za-z0-9_]{3,30}$/;
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function truncatePreview(text, length = 150) {
  const words = text.trim().split(/\s+/);
  let result = [];
  let total = 0;
  for (const word of words) {
    if (total + word.length + (result.length ? 1 : 0) > length) break;
    if (result.length) total += 1;
    total += word.length;
    result.push(word);
  }
  const preview = result.join(" ");
  return preview !== text.trim() ? preview + "..." : preview;
}

function escapeLike(s) {
  return s.replace(/\\/g, "\\\\").replace(/%/g, "\\%").replace(/_/g, "\\_");
}

function safeNext(url) {
  if (!url || !url.startsWith("/") || url.startsWith("//") || url.includes("\\")) return "/";
  return url;
}

async function sign(data, secret) {
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(data));
  return btoa(String.fromCharCode(...new Uint8Array(sig))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function verify(data, sig, secret) {
  const expected = await sign(data, secret);
  if (expected.length !== sig.length) return false;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) diff |= expected.charCodeAt(i) ^ sig.charCodeAt(i);
  return diff === 0;
}

async function parseSession(cookie, secret) {
  if (!cookie) return null;
  const [data, sig] = cookie.split(".");
  if (!data || !sig) return null;
  if (!(await verify(data, sig, secret))) return null;
  try {
    return JSON.parse(atob(data.replace(/-/g, "+").replace(/_/g, "/")));
  } catch { return null; }
}

async function makeSessionCookie(session, secret) {
  const data = btoa(JSON.stringify(session));
  const sig = await sign(data, secret);
  return `${data}.${sig}`;
}

async function hashPassword(password) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt, iterations: 100000, hash: "SHA-256" }, key, 256
  );
  const hash = btoa(String.fromCharCode(...new Uint8Array(bits)));
  const saltB64 = btoa(String.fromCharCode(...salt));
  return `pbkdf2:100000:${saltB64}:${hash}`;
}

async function checkPassword(password, stored) {
  const [, iter, saltB64, hashB64] = stored.split(":");
  const salt = Uint8Array.from(atob(saltB64), (c) => c.charCodeAt(0));
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt, iterations: parseInt(iter), hash: "SHA-256" }, key, 256
  );
  const hash = btoa(String.fromCharCode(...new Uint8Array(bits)));
  return hash === hashB64;
}

function randomToken() {
  const arr = crypto.getRandomValues(new Uint8Array(32));
  return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
}

function securityHeaders(c) {
  c.header("Content-Security-Policy", "default-src 'self'");
  c.header("X-Content-Type-Options", "nosniff");
  c.header("X-Frame-Options", "DENY");
}

function layout(c, title, body, session) {
  securityHeaders(c);
  const user = session?.username;
  const csrf = session?.csrf || "";
  return c.html(html`<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>${title} — Blog</title>
<link rel="stylesheet" href="/style.css">
<script src="/theme.js" defer></script>
</head><body>
<header class="site-header"><div class="container header-inner">
<a href="/" class="logo">Blog</a>
<nav class="nav-links">
<a href="/">Home</a><a href="/search">Search</a>
${user ? raw(`<a href="/new">New Post</a><span class="nav-user">${escapeHtml(user)}</span>
<form method="post" action="/logout" class="logout-form"><input type="hidden" name="csrf_token" value="${csrf}">
<button type="submit" class="btn btn-ghost">Log out</button></form>`)
: raw(`<a href="/login">Log in</a><a href="/signup" class="btn btn-primary">Sign up</a>`)}
</nav>
<button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">🌓</button>
</div></header>
<main class="container main-content">${body}</main>
<footer class="site-footer"><div class="container"><p>A simple personal blog — share your thoughts.</p></div></footer>
</body></html>`);
}

async function getSession(c) {
  const secret = c.env.SECRET_KEY || "dev";
  const cookie = getCookie(c, "session");
  return (await parseSession(cookie, secret)) || { csrf: randomToken() };
}

async function saveSession(c, session) {
  const secret = c.env.SECRET_KEY || "dev";
  const val = await makeSessionCookie(session, secret);
  setCookie(c, "session", val, { httpOnly: true, sameSite: "Lax", secure: true, path: "/" });
}

app.use("*", async (c, next) => {
  if (["POST", "PUT", "PATCH", "DELETE"].includes(c.req.method)) {
    const session = await getSession(c);
    let token = c.req.header("X-CSRF-Token");
    if (!token) {
      const ct = c.req.header("content-type") || "";
      if (ct.includes("application/json")) {
        const clone = c.req.raw.clone();
        try {
          const json = await clone.json();
          token = json?.csrf_token;
        } catch { /* ignore */ }
      } else if (ct.includes("application/x-www-form-urlencoded") || ct.includes("multipart/form-data")) {
        const fd = await c.req.parseBody();
        c.set("parsedBody", fd);
        token = fd?.csrf_token;
      }
    }
    if (!token || token !== session.csrf) {
      securityHeaders(c);
      if (c.req.path.startsWith("/api/")) {
        return c.json({ ok: false, error: "Invalid or missing CSRF token." }, 400);
      }
      return c.text("Invalid or missing CSRF token.", 400);
    }
    c.set("session", session);
  }
  await next();
});

app.get("/", async (c) => {
  const session = await getSession(c);
  await saveSession(c, session);
  const { results } = await c.env.DB.prepare(
    "SELECT p.*, u.username AS author FROM posts p JOIN users u ON p.author_id = u.id ORDER BY p.created_at DESC, p.id DESC"
  ).all();
  const cards = (results || []).map((p) => raw(`
<article class="post-card"><h2><a href="/post/${p.id}">${escapeHtml(p.title)}</a></h2>
<p class="post-preview">${escapeHtml(truncatePreview(p.body))}</p>
<div class="post-meta"><span class="post-author">${escapeHtml(p.author)}</span>
<time datetime="${p.created_at}">${p.created_at}</time></div></article>`)).join("");
  const body = results?.length
    ? raw(`<h1 class="page-title">Latest Posts</h1><div class="post-list">${cards}</div>`)
    : raw(`<h1 class="page-title">Latest Posts</h1><div class="empty-state"><p>No posts yet. Be the first to write something!</p>
${session.user_id ? '<a href="/new" class="btn btn-primary">Write a post</a>' : '<a href="/signup" class="btn btn-primary">Sign up to post</a>'}</div>`);
  return layout(c, "Home", body, session);
});

app.get("/signup", async (c) => {
  const session = await getSession(c);
  await saveSession(c, session);
  return layout(c, "Sign up", raw(`
<div class="auth-form"><h1>Sign up</h1>
<form method="post" action="/signup"><input type="hidden" name="csrf_token" value="${session.csrf}">
<div class="form-group"><label for="username">Username</label>
<input type="text" id="username" name="username" required pattern="[A-Za-z0-9_]{3,30}" maxlength="30"></div>
<div class="form-group"><label for="email">Email</label><input type="email" id="email" name="email" required></div>
<div class="form-group"><label for="password">Password</label><input type="password" id="password" name="password" required minlength="8"></div>
<button type="submit" class="btn btn-primary">Create account</button></form>
<p class="form-hint">Already have an account? <a href="/login">Log in</a></p></div>`), session);
});

app.post("/signup", async (c) => {
  const session = c.get("session") || await getSession(c);
  const fd = c.get("parsedBody") || await c.req.parseBody();
  const username = String(fd.username || "").trim();
  const email = String(fd.email || "").trim();
  const password = String(fd.password || "");
  const errors = [];
  if (!USERNAME_RE.test(username)) errors.push("Username must be 3-30 letters, digits, or underscores.");
  else {
    const ex = await c.env.DB.prepare("SELECT id FROM users WHERE username = ? COLLATE NOCASE").bind(username).first();
    if (ex) errors.push("That username is already taken.");
  }
  if (!EMAIL_RE.test(email)) errors.push("Please enter a valid email address.");
  else {
    const ex = await c.env.DB.prepare("SELECT id FROM users WHERE email = ?").bind(email.toLowerCase()).first();
    if (ex) errors.push("That email is already registered.");
  }
  if (!password || password.length < 8) errors.push("Password must be at least 8 characters.");
  if (errors.length) {
    securityHeaders(c);
    const errHtml = errors.map((e) => `<li>${escapeHtml(e)}</li>`).join("");
    return c.html(`<!DOCTYPE html><body><ul class="form-errors">${errHtml}</ul></body>`, 400);
  }
  const hash = await hashPassword(password);
  try {
    await c.env.DB.prepare("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)")
      .bind(username, email.toLowerCase(), hash).run();
  } catch {
    return c.text("Registration failed.", 400);
  }
  return c.redirect("/login", 302);
});

app.get("/login", async (c) => {
  const session = await getSession(c);
  await saveSession(c, session);
  const next = c.req.query("next") || "/";
  return layout(c, "Log in", raw(`
<div class="auth-form"><h1>Log in</h1>
<form method="post" action="/login?next=${encodeURIComponent(next)}">
<input type="hidden" name="csrf_token" value="${session.csrf}">
<input type="hidden" name="next" value="${escapeHtml(next)}">
<div class="form-group"><label for="username">Username</label><input type="text" id="username" name="username" required></div>
<div class="form-group"><label for="password">Password</label><input type="password" id="password" name="password" required></div>
<button type="submit" class="btn btn-primary">Log in</button></form>
<p class="form-hint">No account? <a href="/signup">Sign up</a></p></div>`), session);
});

app.post("/login", async (c) => {
  const session = c.get("session") || await getSession(c);
  const fd = c.get("parsedBody") || await c.req.parseBody();
  const username = String(fd.username || "").trim();
  const password = String(fd.password || "");
  const next = safeNext(String(fd.next || "/"));
  const user = await c.env.DB.prepare("SELECT * FROM users WHERE username = ? COLLATE NOCASE").bind(username).first();
  if (!user || !(await checkPassword(password, user.password_hash))) {
    securityHeaders(c);
    return c.text("Invalid username or password.", 400);
  }
  session.user_id = user.id;
  session.username = user.username;
  session.csrf = randomToken();
  await saveSession(c, session);
  return c.redirect(next, 302);
});

app.post("/logout", async (c) => {
  deleteCookie(c, "session", { path: "/" });
  return c.redirect("/", 302);
});

app.get("/post/:id", async (c) => {
  const session = await getSession(c);
  await saveSession(c, session);
  const id = c.req.param("id");
  const post = await c.env.DB.prepare(
    "SELECT p.*, u.username AS author FROM posts p JOIN users u ON p.author_id = u.id WHERE p.id = ?"
  ).bind(id).first();
  if (!post) return c.text("Not found", 404);
  const comments = await c.env.DB.prepare(
    "SELECT c.*, u.username AS author FROM comments c JOIN users u ON c.user_id = u.id WHERE c.post_id = ? ORDER BY c.created_at ASC, c.id ASC"
  ).bind(id).all();
  const likes = await c.env.DB.prepare("SELECT COUNT(*) AS n FROM reactions WHERE post_id = ? AND kind = 'like'").bind(id).first();
  const dislikes = await c.env.DB.prepare("SELECT COUNT(*) AS n FROM reactions WHERE post_id = ? AND kind = 'dislike'").bind(id).first();
  let userReaction = null;
  if (session.user_id) {
    const r = await c.env.DB.prepare("SELECT kind FROM reactions WHERE post_id = ? AND user_id = ?").bind(id, session.user_id).first();
    userReaction = r?.kind || null;
  }
  const commentHtml = (comments.results || []).map((cm) => raw(`
<li class="comment"><div class="comment-meta"><strong>${escapeHtml(cm.author)}</strong>
<time datetime="${cm.created_at}">${cm.created_at}</time></div>
<p class="comment-body">${escapeHtml(cm.body)}</p></li>`)).join("");
  const isAuthor = session.username === post.author;
  return layout(c, post.title, raw(`
<script src="/post.js" defer></script>
<article class="post-detail"><h1>${escapeHtml(post.title)}</h1>
<div class="post-meta"><span class="post-author">${escapeHtml(post.author)}</span>
<time datetime="${post.created_at}">${post.created_at}</time>
${post.updated_at ? '<span class="edited-marker">(edited)</span>' : ""}</div>
<div class="post-body">${escapeHtml(post.body)}</div>
${isAuthor ? raw(`<div class="post-actions"><a href="/edit/${post.id}" class="btn btn-secondary">Edit</a>
<form method="post" action="/delete/${post.id}" class="delete-form"><input type="hidden" name="csrf_token" value="${session.csrf}">
<button type="submit" class="btn btn-danger" id="delete-btn">Delete</button></form></div>`) : ""}
<section class="reactions" id="reactions" data-post-id="${post.id}" data-csrf="${session.csrf}">
<button type="button" class="reaction-btn ${userReaction === "like" ? "active" : ""}" data-kind="like" id="like-btn">👍 <span id="like-count">${likes?.n || 0}</span></button>
<button type="button" class="reaction-btn ${userReaction === "dislike" ? "active" : ""}" data-kind="dislike" id="dislike-btn">👎 <span id="dislike-count">${dislikes?.n || 0}</span></button>
</section>
<section class="comments-section"><h2>Comments</h2><ul id="comment-list" class="comment-list">${commentHtml}</ul>
${session.user_id ? raw(`<form id="comment-form" class="comment-form" data-post-id="${post.id}" data-csrf="${session.csrf}">
<label for="comment-body">Add a comment</label><textarea id="comment-body" name="body" rows="3" maxlength="2000" required></textarea>
<button type="submit" class="btn btn-primary">Post comment</button><p id="comment-error" class="form-error" hidden></p></form>`)
: raw(`<p class="comment-login-prompt"><a href="/login?next=/post/${post.id}">Log in</a> to leave a comment.</p>`)}
</section></article>`), session);
});

app.get("/new", async (c) => {
  const session = await getSession(c);
  if (!session.user_id) return c.redirect("/login?next=/new", 302);
  await saveSession(c, session);
  return layout(c, "New Post", raw(`
<div class="edit-form"><h1>New Post</h1>
<form method="post" action="/new"><input type="hidden" name="csrf_token" value="${session.csrf}">
<div class="form-group"><label for="title">Title</label><input type="text" id="title" name="title" required maxlength="200"></div>
<div class="form-group"><label for="body">Body</label><textarea id="body" name="body" rows="12" required maxlength="20000"></textarea></div>
<button type="submit" class="btn btn-primary">Publish</button></form></div>`), session);
});

app.post("/new", async (c) => {
  const session = c.get("session") || await getSession(c);
  if (!session.user_id) return c.redirect("/login?next=/new", 302);
  const fd = c.get("parsedBody") || await c.req.parseBody();
  const title = String(fd.title || "").trim();
  const body = String(fd.body || "").trim();
  if (!title || !body) return c.text("Validation error", 400);
  const r = await c.env.DB.prepare("INSERT INTO posts (author_id, title, body) VALUES (?, ?, ?)")
    .bind(session.user_id, title, body).run();
  return c.redirect(`/post/${r.meta.last_row_id}`, 302);
});

app.get("/search", async (c) => {
  const session = await getSession(c);
  await saveSession(c, session);
  const q = (c.req.query("q") || "").trim().slice(0, 100);
  if (!q) {
    return layout(c, "Search", raw(`
<h1 class="page-title">Search</h1>
<form method="get" action="/search" class="search-form"><label for="search-q">Search posts</label>
<div class="search-row"><input type="search" id="search-q" name="q" maxlength="100" placeholder="Search by title or body…">
<button type="submit" class="btn btn-primary">Search</button></div></form>
<div class="empty-state"><p>Enter a search term to find posts.</p></div>`), session);
  }
  const pattern = `%${escapeLike(q)}%`;
  const { results } = await c.env.DB.prepare(
    "SELECT p.*, u.username AS author FROM posts p JOIN users u ON p.author_id = u.id WHERE p.title LIKE ? ESCAPE '\\\\' OR p.body LIKE ? ESCAPE '\\\\' ORDER BY p.created_at DESC, p.id DESC"
  ).bind(pattern, pattern).all();
  const cards = (results || []).map((p) => raw(`
<article class="post-card"><h2><a href="/post/${p.id}">${escapeHtml(p.title)}</a></h2>
<p class="post-preview">${escapeHtml(truncatePreview(p.body))}</p>
<div class="post-meta"><span class="post-author">${escapeHtml(p.author)}</span>
<time datetime="${p.created_at}">${p.created_at}</time></div></article>`)).join("");
  const body = results?.length
    ? raw(`<h1 class="page-title">Search</h1><form method="get" action="/search" class="search-form"><div class="search-row"><input type="search" name="q" value="${escapeHtml(q)}" maxlength="100"><button type="submit" class="btn btn-primary">Search</button></div></form><div class="post-list">${cards}</div>`)
    : raw(`<h1 class="page-title">Search</h1><div class="empty-state"><p>No posts match "${escapeHtml(q)}".</p></div>`);
  return layout(c, "Search", body, session);
});

app.post("/api/post/:id/comment", async (c) => {
  const session = c.get("session") || await getSession(c);
  if (!session.user_id) return c.json({ ok: false, error: "Please log in first." }, 401);
  const id = c.req.param("id");
  const post = await c.env.DB.prepare("SELECT id FROM posts WHERE id = ?").bind(id).first();
  if (!post) return c.json({ ok: false, error: "Post not found." }, 404);
  const { body } = await c.req.json();
  if (typeof body !== "string") return c.json({ ok: false, error: "Comment must be text." }, 400);
  const text = body.trim();
  if (!text) return c.json({ ok: false, error: "Comment cannot be empty." }, 400);
  if (text.length > 2000) return c.json({ ok: false, error: "Comment must be at most 2000 characters." }, 400);
  const r = await c.env.DB.prepare("INSERT INTO comments (post_id, user_id, body) VALUES (?, ?, ?)")
    .bind(id, session.user_id, text).run();
  const comment = await c.env.DB.prepare(
    "SELECT c.*, u.username AS author FROM comments c JOIN users u ON c.user_id = u.id WHERE c.id = ?"
  ).bind(r.meta.last_row_id).first();
  return c.json({ ok: true, comment }, 201);
});

app.post("/api/post/:id/react", async (c) => {
  const session = c.get("session") || await getSession(c);
  if (!session.user_id) return c.json({ ok: false, error: "Please log in first." }, 401);
  const id = c.req.param("id");
  const post = await c.env.DB.prepare("SELECT id FROM posts WHERE id = ?").bind(id).first();
  if (!post) return c.json({ ok: false, error: "Post not found." }, 404);
  const { kind } = await c.req.json();
  if (kind !== "like" && kind !== "dislike") return c.json({ ok: false, error: "Reaction must be 'like' or 'dislike'." }, 400);
  const existing = await c.env.DB.prepare("SELECT id, kind FROM reactions WHERE post_id = ? AND user_id = ?")
    .bind(id, session.user_id).first();
  let result = kind;
  if (existing) {
    if (existing.kind === kind) {
      await c.env.DB.prepare("DELETE FROM reactions WHERE id = ?").bind(existing.id).run();
      result = null;
    } else {
      await c.env.DB.prepare("UPDATE reactions SET kind = ? WHERE id = ?").bind(kind, existing.id).run();
    }
  } else {
    await c.env.DB.prepare("INSERT INTO reactions (post_id, user_id, kind) VALUES (?, ?, ?)")
      .bind(id, session.user_id, kind).run();
  }
  const likes = await c.env.DB.prepare("SELECT COUNT(*) AS n FROM reactions WHERE post_id = ? AND kind = 'like'").bind(id).first();
  const dislikes = await c.env.DB.prepare("SELECT COUNT(*) AS n FROM reactions WHERE post_id = ? AND kind = 'dislike'").bind(id).first();
  return c.json({ ok: true, reaction: result, counts: { like: likes?.n || 0, dislike: dislikes?.n || 0 } });
});

app.get("/edit/:id", async (c) => {
  const session = await getSession(c);
  if (!session.user_id) return c.redirect(`/login?next=/edit/${c.req.param("id")}`, 302);
  const post = await c.env.DB.prepare("SELECT * FROM posts WHERE id = ?").bind(c.req.param("id")).first();
  if (!post) return c.text("Not found", 404);
  if (post.author_id !== session.user_id) return c.text("Forbidden", 403);
  await saveSession(c, session);
  return layout(c, "Edit Post", raw(`
<div class="edit-form"><h1>Edit Post</h1>
<form method="post" action="/edit/${post.id}"><input type="hidden" name="csrf_token" value="${session.csrf}">
<div class="form-group"><label for="title">Title</label><input type="text" id="title" name="title" value="${escapeHtml(post.title)}" required maxlength="200"></div>
<div class="form-group"><label for="body">Body</label><textarea id="body" name="body" rows="12" required maxlength="20000">${escapeHtml(post.body)}</textarea></div>
<button type="submit" class="btn btn-primary">Save changes</button></form></div>`), session);
});

app.post("/edit/:id", async (c) => {
  const session = c.get("session") || await getSession(c);
  if (!session.user_id) return c.redirect(`/login?next=/edit/${c.req.param("id")}`, 302);
  const post = await c.env.DB.prepare("SELECT * FROM posts WHERE id = ?").bind(c.req.param("id")).first();
  if (!post) return c.text("Not found", 404);
  if (post.author_id !== session.user_id) return c.text("Forbidden", 403);
  const fd = c.get("parsedBody") || await c.req.parseBody();
  const title = String(fd.title || "").trim();
  const body = String(fd.body || "").trim();
  if (!title || !body) return c.text("Validation error", 400);
  await c.env.DB.prepare("UPDATE posts SET title = ?, body = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?")
    .bind(title, body, post.id).run();
  return c.redirect(`/post/${post.id}`, 302);
});

app.post("/delete/:id", async (c) => {
  const session = c.get("session") || await getSession(c);
  if (!session.user_id) return c.redirect(`/login?next=/post/${c.req.param("id")}`, 302);
  const post = await c.env.DB.prepare("SELECT * FROM posts WHERE id = ?").bind(c.req.param("id")).first();
  if (!post) return c.text("Not found", 404);
  if (post.author_id !== session.user_id) return c.text("Forbidden", 403);
  await c.env.DB.prepare("DELETE FROM posts WHERE id = ?").bind(post.id).run();
  return c.redirect("/", 302);
});

export default app;
