import os
import tempfile

import pytest

from app import create_app
from db import init_db


@pytest.fixture
def csrf_client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    os.environ["DATABASE"] = db_path
    import db as db_module
    db_module.DATABASE = db_path
    application = create_app({"TESTING": True, "SKIP_INIT_DB": True})
    init_db()
    yield application.test_client()
    os.unlink(db_path)


def test_post_without_csrf_returns_400(csrf_client):
    resp = csrf_client.post("/signup", data={
        "username": "test",
        "email": "test@example.com",
        "password": "password123",
    })
    assert resp.status_code == 400


def test_api_without_csrf_returns_400_json(csrf_client):
    resp = csrf_client.post(
        "/api/post/1/comment",
        json={"body": "hello"},
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["ok"] is False
