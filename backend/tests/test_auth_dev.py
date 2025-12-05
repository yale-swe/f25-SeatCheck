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
    # redirect should include token parameter
    assert "token=" in response.headers["location"]
    assert response.headers["location"].startswith("http://localhost:8081/")

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
    # Clear any existing session first
    client.post("/auth/dev/logout", follow_redirects=False)
    # without login, /auth/me should raise 401
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_map_requires_login():
    client = TestClient(app)

    # w/o login, accessing /map should result in 401
    r0 = client.get("/map")
    assert r0.status_code in (401, 307)

    # after dev login, should be accessible
    client.get("/auth/dev/login?netid=mapuser", follow_redirects=False)
    r = client.get("/map")
    assert r.status_code == 200
    assert "SeatCheck Map" in r.text
