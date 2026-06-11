import os
import tempfile

import pytest

from app import create_app
from db import init_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    os.environ["DATABASE"] = db_path
    import db as db_module
    db_module.DATABASE = db_path
    application = create_app({
        "TESTING": True,
        "DISABLE_CSRF": True,
        "SKIP_INIT_DB": True,
    })
    init_db()
    yield application
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post("/signup", data={
        "username": "alice",
        "email": "alice@example.com",
        "password": "password123",
        "csrf_token": _get_csrf(client),
    })
    client.post("/login", data={
        "username": "alice",
        "password": "password123",
        "csrf_token": _get_csrf(client),
    })
    return client


def _get_csrf(client):
    resp = client.get("/login")
    import re
    match = re.search(r'name="csrf_token" value="([^"]+)"', resp.data.decode())
    return match.group(1) if match else ""
