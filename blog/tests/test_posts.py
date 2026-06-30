def test_create_edit_delete_post(auth_client):
    csrf = _csrf(auth_client, "/new")
    resp = auth_client.post("/new", data={
        "title": "Hello World",
        "body": "This is my first post.",
        "csrf_token": csrf,
    })
    assert resp.status_code == 302
    post_id = int(resp.headers["Location"].split("/")[-1])

    resp = auth_client.get(f"/post/{post_id}")
    assert resp.status_code == 200
    assert b"Hello World" in resp.data

    csrf = _csrf(auth_client, f"/edit/{post_id}")
    resp = auth_client.post(f"/edit/{post_id}", data={
        "title": "Updated Title",
        "body": "Updated body.",
        "csrf_token": csrf,
    })
    assert resp.status_code == 302

    resp = auth_client.get(f"/post/{post_id}")
    assert b"(edited)" in resp.data

    csrf = _csrf(auth_client, f"/post/{post_id}")
    resp = auth_client.post(f"/delete/{post_id}", data={"csrf_token": csrf})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_non_author_gets_403(client, auth_client):
    csrf = _csrf(auth_client, "/new")
    resp = auth_client.post("/new", data={
        "title": "Private",
        "body": "Secret content here.",
        "csrf_token": csrf,
    })
    post_id = int(resp.headers["Location"].split("/")[-1])

    csrf2 = _csrf(client, "/signup")
    client.post("/signup", data={
        "username": "eve",
        "email": "eve@example.com",
        "password": "password123",
        "csrf_token": csrf2,
    })
    csrf2 = _csrf(client, "/login")
    client.post("/login", data={
        "username": "eve",
        "password": "password123",
        "csrf_token": csrf2,
    })

    resp = client.get(f"/edit/{post_id}")
    assert resp.status_code == 403


def test_validation_errors(auth_client):
    csrf = _csrf(auth_client, "/new")
    resp = auth_client.post("/new", data={
        "title": "",
        "body": "",
        "csrf_token": csrf,
    })
    assert resp.status_code == 400


def test_unknown_post_404(client):
    resp = client.get("/post/99999")
    assert resp.status_code == 404


def test_new_post_page_has_quill_editor(auth_client):
    resp = auth_client.get("/new")
    assert resp.status_code == 200
    assert b"quill-editor" in resp.data
    assert b"vendor/quill/quill.js" in resp.data
    assert b'rows="12"' not in resp.data


def _csrf(client, path):
    import re
    resp = client.get(path)
    match = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode())
    return match.group(1) if match else ""
