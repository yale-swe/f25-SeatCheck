import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(autouse=True)
def enable_dev_auth(monkeypatch):
    """Force DEV_AUTH=1 for these tests."""
    monkeypatch.setenv("DEV_AUTH", "1")
    yield
    monkeypatch.delenv("DEV_AUTH", raising=False)


client = TestClient(app)


def test_dev_login_and_whoami():
    # dev login
    response = client.get("/auth/dev/login?netid=dev001", follow_redirects=False)
    assert response.status_code == 302  # redirect
    assert response.headers["location"].endswith("/")  # redirect to home

    # whoami (session should persist)
    whoami = client.get("/debug/whoami", follow_redirects=False)
    assert whoami.status_code == 200
    assert whoami.json()["netid"] == "dev001"

    # /auth/me (should also return netid)
    me = client.get("/auth/me", follow_redirects=False)
    assert me.status_code == 200
    assert me.json()["netid"] == "dev001"

    # logout
    logout = client.post("/auth/dev/logout", follow_redirects=False)
    assert logout.status_code == 200
    assert logout.json() == {"ok": True}

    # whoami after logout should be cleared
    whoami_after = client.get("/debug/whoami", follow_redirects=False)
    assert whoami_after.status_code == 200
    assert whoami_after.json()["netid"] is None


def test_auth_me_requires_login():
    # without login, /auth/me should raise 401
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
