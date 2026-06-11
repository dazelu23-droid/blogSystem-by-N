def test_empty_query_shows_prompt(client):
    resp = client.get("/search")
    assert resp.status_code == 200
    assert b"Enter a search term" in resp.data


def test_search_finds_posts(auth_client):
    csrf = _csrf(auth_client, "/new")
    auth_client.post("/new", data={
        "title": "Python Tips",
        "body": "Learn Python programming today.",
        "csrf_token": csrf,
    })
    resp = auth_client.get("/search?q=python")
    assert resp.status_code == 200
    assert b"Python Tips" in resp.data


def test_search_wildcard_literal(auth_client):
    csrf = _csrf(auth_client, "/new")
    auth_client.post("/new", data={
        "title": "100% Complete",
        "body": "Nothing here matches underscore.",
        "csrf_token": csrf,
    })
    resp = auth_client.get("/search?q=%")
    assert resp.status_code == 200
    assert b"100% Complete" in resp.data
    resp = auth_client.get("/search?q=_")
    assert b"No posts match" in resp.data or b"100% Complete" not in resp.data


def _csrf(client, path):
    import re
    resp = client.get(path)
    match = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode())
    return match.group(1) if match else ""
