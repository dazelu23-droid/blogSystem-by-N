def test_like_and_toggle(auth_client):
    post_id = _create_post(auth_client)
    csrf = _api_csrf(auth_client, post_id)

    resp = auth_client.post(
        f"/api/post/{post_id}/react",
        json={"kind": "like"},
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["reaction"] == "like"
    assert data["counts"]["like"] == 1

    resp = auth_client.post(
        f"/api/post/{post_id}/react",
        json={"kind": "like"},
        headers={"X-CSRF-Token": csrf},
    )
    data = resp.get_json()
    assert data["reaction"] is None
    assert data["counts"]["like"] == 0


def test_switch_reaction(auth_client):
    post_id = _create_post(auth_client)
    csrf = _api_csrf(auth_client, post_id)

    auth_client.post(
        f"/api/post/{post_id}/react",
        json={"kind": "like"},
        headers={"X-CSRF-Token": csrf},
    )
    resp = auth_client.post(
        f"/api/post/{post_id}/react",
        json={"kind": "dislike"},
        headers={"X-CSRF-Token": csrf},
    )
    data = resp.get_json()
    assert data["reaction"] == "dislike"
    assert data["counts"]["like"] == 0
    assert data["counts"]["dislike"] == 1


def test_bad_kind_400(auth_client):
    post_id = _create_post(auth_client)
    csrf = _api_csrf(auth_client, post_id)
    resp = auth_client.post(
        f"/api/post/{post_id}/react",
        json={"kind": "love"},
        headers={"X-CSRF-Token": csrf},
    )
    assert resp.status_code == 400


def _create_post(client):
    csrf = _csrf(client, "/new")
    resp = client.post("/new", data={
        "title": "React Test",
        "body": "Body.",
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
