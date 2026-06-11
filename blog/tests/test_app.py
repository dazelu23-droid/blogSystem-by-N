def test_home_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
