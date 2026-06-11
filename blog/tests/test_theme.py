def test_theme_toggle_present(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b'id="theme-toggle"' in resp.data
    assert b"theme.js" in resp.data
