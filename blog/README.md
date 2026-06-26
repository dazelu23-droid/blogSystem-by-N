# Blog

A complete personal blog built with Flask, SQLite, and Jinja2 templates.

## Features

- User sign up / log in / log out (username-based, case-insensitive)
- Create, edit, and delete posts (author only)
- Comments and like/dislike reactions (JSON API)
- Case-insensitive search with wildcard escaping
- Light/dark theme toggle (localStorage)
- Password reset via email link
- CSRF protection on all state-changing requests
- Security headers (CSP, X-Frame-Options, nosniff)

## Quick Start (Local)

```bash
cd blog
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5001

### Password reset email (optional)

Set SMTP environment variables to send reset links by email:

- `SMTP_HOST`, `SMTP_PORT` (default `587`)
- `SMTP_USER`, `SMTP_PASSWORD`
- `SMTP_FROM` (optional sender address)
- `SMTP_TLS` (default `1`)

For the Cloudflare Workers deployment, set `RESEND_API_KEY` and `SMTP_FROM` instead.

## Run Tests

```bash
cd blog
python -m pytest tests/ -v
```

## Live Site (Workers + D1)

**https://simple-blog-by-n.dazelu.workers.dev**

Redeploy:

```bash
cd blog-workers
npx wrangler deploy
```

## Project Structure

```
blog/           Flask app + pytest tests
blog-workers/   Cloudflare Workers + D1 port
task-11.md      Design spec and grading contracts
```
