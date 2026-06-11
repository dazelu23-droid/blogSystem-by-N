def test_add_comment(auth_client):
    post_id = _create_post(auth_client)
    csrf = _api_csrf(auth_client, post_id)
    resp = auth_client.post(
        f"/api/post/{post_id}/comment",
        json={"body": "Nice post!"},
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["ok"] is True
    assert data["comment"]["body"] == "Nice post!"


def test_comment_guest_401(app, auth_client):
    post_id = _create_post(auth_client)
    guest = app.test_client()
    csrf = _csrf(guest, "/login")
    resp = guest.post(
        f"/api/post/{post_id}/comment",
        json={"body": "Hello"},
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 401


def test_comment_empty_400(auth_client):
    post_id = _create_post(auth_client)
    csrf = _api_csrf(auth_client, post_id)
    resp = auth_client.post(
        f"/api/post/{post_id}/comment",
        json={"body": "   "},
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 400


def test_comment_not_found(auth_client):
    csrf = _csrf(auth_client, "/")
    resp = auth_client.post(
        "/api/post/99999/comment",
        json={"body": "Hello"},
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 404


def _create_post(client):
    csrf = _csrf(client, "/new")
    resp = client.post("/new", data={
        "title": "Test Post",
        "body": "Body text.",
        "csrf_token": csrf,
    })
    return int(resp.headers["Location"].split("/")[-1])


def _csrf(client, path):
    import re
    resp = client.get(path)
    match = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode())
    return match.group(1) if match else ""


def _api_csrf(client, post_id):
    import re
    resp = client.get(f"/post/{post_id}")
    match = re.search(r'data-csrf="([^"]+)"', resp.data.decode())
    return match.group(1) if match else ""
