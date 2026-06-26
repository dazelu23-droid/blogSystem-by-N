def test_signup_and_login(client):
    csrf = _csrf(client, "/signup")
    resp = client.post("/signup", data={
        "username": "bob",
        "email": "bob@example.com",
        "password": "password123",
        "csrf_token": csrf,
    })
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

    csrf = _csrf(client, "/login")
    resp = client.post("/login", data={
        "username": "bob",
        "password": "password123",
        "csrf_token": csrf,
    })
    assert resp.status_code == 302


def test_duplicate_username_case_insensitive(client):
    csrf = _csrf(client, "/signup")
    client.post("/signup", data={
        "username": "Alice",
        "email": "alice@example.com",
        "password": "password123",
        "csrf_token": csrf,
    })
    csrf = _csrf(client, "/signup")
    resp = client.post("/signup", data={
        "username": "alice",
        "email": "alice2@example.com",
        "password": "password123",
        "csrf_token": csrf,
    })
    assert resp.status_code == 400


def test_wrong_password(client):
    csrf = _csrf(client, "/signup")
    client.post("/signup", data={
        "username": "carol",
        "email": "carol@example.com",
        "password": "password123",
        "csrf_token": csrf,
    })
    csrf = _csrf(client, "/login")
    resp = client.post("/login", data={
        "username": "carol",
        "password": "wrongpass",
        "csrf_token": csrf,
    })
    assert resp.status_code == 400


def test_logout(auth_client):
    csrf = _csrf(auth_client, "/")
    resp = auth_client.post("/logout", data={"csrf_token": csrf})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_protected_route_redirects_guest(client):
    resp = client.get("/new")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    assert "next=%2Fnew" in resp.headers["Location"] or "next=/new" in resp.headers["Location"]


def test_open_redirect_blocked(client):
    csrf = _csrf(client, "/signup")
    client.post("/signup", data={
        "username": "dave",
        "email": "dave@example.com",
        "password": "password123",
        "csrf_token": csrf,
    })
    csrf = _csrf(client, "/login?next=//evil.com")
    resp = client.post("/login?next=//evil.com", data={
        "username": "dave",
        "password": "password123",
        "csrf_token": csrf,
        "next": "//evil.com",
    })
    assert resp.status_code == 302
    loc = resp.headers["Location"]
    assert "evil.com" not in loc


def test_password_reset_flow(client):
    import re

    csrf = _csrf(client, "/signup")
    client.post("/signup", data={
        "username": "bob",
        "email": "bob@example.com",
        "password": "password123",
        "csrf_token": csrf,
    })

    csrf = _csrf(client, "/forgot-password")
    resp = client.post("/forgot-password", data={
        "email": "bob@example.com",
        "csrf_token": csrf,
    })
    assert resp.status_code == 200
    match = re.search(r'href="(/reset-password/[^"]+)"', resp.data.decode())
    assert match
    reset_path = match.group(1)

    resp = client.get(reset_path)
    assert resp.status_code == 200

    resp = client.post(reset_path, data={
        "password": "newpassword1",
        "password_confirm": "newpassword1",
        "csrf_token": csrf,
    })
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

    resp = client.post("/login", data={
        "username": "bob",
        "password": "newpassword1",
        "csrf_token": csrf,
    })
    assert resp.status_code == 302

    resp = client.post("/login", data={
        "username": "bob",
        "password": "password123",
        "csrf_token": csrf,
    })
    assert resp.status_code == 400


def test_password_reset_unknown_email(client):
    csrf = _csrf(client, "/forgot-password")
    resp = client.post("/forgot-password", data={
        "email": "nobody@example.com",
        "csrf_token": csrf,
    })
    assert resp.status_code == 200
    assert b"If that email is registered" in resp.data


def test_password_reset_invalid_token(client):
    resp = client.get("/reset-password/not-a-real-token")
    assert resp.status_code == 400
    assert b"invalid or has expired" in resp.data.lower()


def test_password_reset_mismatch(client):
    import re

    csrf = _csrf(client, "/signup")
    client.post("/signup", data={
        "username": "erin",
        "email": "erin@example.com",
        "password": "password123",
        "csrf_token": csrf,
    })
    csrf = _csrf(client, "/forgot-password")
    resp = client.post("/forgot-password", data={
        "email": "erin@example.com",
        "csrf_token": csrf,
    })
    reset_path = re.search(r'href="(/reset-password/[^"]+)"', resp.data.decode()).group(1)
    resp = client.post(reset_path, data={
        "password": "newpassword1",
        "password_confirm": "different1",
        "csrf_token": csrf,
    })
    assert resp.status_code == 400
    assert b"do not match" in resp.data.lower()


def _csrf(client, path):
    import re
    resp = client.get(path)
    match = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode())
    return match.group(1) if match else ""
