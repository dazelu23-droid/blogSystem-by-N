"""Smoke tests for theme/font dropdown UI and static assets."""
import re

from app import create_app


ROUTES = ["/", "/login", "/signup", "/search"]


def test_theme_and_font_dropdowns_on_all_pages(client):
    for route in ROUTES:
        resp = client.get(route)
        assert resp.status_code == 200, route
        html = resp.data.decode()

        assert 'id="theme-toggle"' in html, route
        assert 'id="theme-menu"' in html, route
        assert 'id="font-toggle"' in html, route
        assert 'id="font-menu"' in html, route
        assert 'data-theme="ocean"' in html, route
        assert 'data-font="mono"' in html, route
        assert "theme.js" in html, route


def test_static_theme_js_has_dropdown_logic():
    app = create_app({"TESTING": True, "SKIP_INIT_DB": True})
    client = app.test_client()

    resp = client.get("/static/theme.js")
    assert resp.status_code == 200
    js = resp.data.decode()
    assert "blog-theme" in js
    assert "blog-font" in js
    assert "midnight" in js
    assert "elegant" in js
    assert "applyTheme" in js
    assert "applyFont" in js


def test_static_css_has_all_themes_and_fonts():
    app = create_app({"TESTING": True, "SKIP_INIT_DB": True})
    client = app.test_client()

    resp = client.get("/static/style.css")
    assert resp.status_code == 200
    css = resp.data.decode()

    for theme in ("light", "dark", "ocean", "forest", "sunset", "lavender", "midnight"):
        assert f'[data-theme="{theme}"]' in css

    for font in ("system", "serif", "mono", "rounded", "elegant", "classic"):
        assert f'[data-font="{font}"]' in css

    assert ".pref-dropdown" in css
    assert ".pref-menu" in css


def test_end_to_end_signup_post_with_dropdowns_present():
    app = create_app({"TESTING": True, "DISABLE_CSRF": True})
    client = app.test_client()

    client.post("/signup", data={
        "username": "smokeuser",
        "email": "smoke@example.com",
        "password": "password123",
    })
    client.post("/login", data={
        "username": "smokeuser",
        "password": "password123",
    })
    client.post("/new", data={
        "title": "Smoke test post",
        "body": "Testing appearance dropdowns on post page.",
    })

    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Smoke test post" in resp.data
    assert b'id="font-toggle"' in resp.data

    post_id = re.search(r'href="/post/(\d+)"', resp.data.decode())
    assert post_id, "expected post link on home page"

    post_resp = client.get(f"/post/{post_id.group(1)}")
    assert post_resp.status_code == 200
    assert b'id="theme-menu"' in post_resp.data
    assert b"post.js" in post_resp.data
