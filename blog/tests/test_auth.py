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


def _csrf(client, path):
    import re
    resp = client.get(path)
    match = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode())
    return match.group(1) if match else ""
