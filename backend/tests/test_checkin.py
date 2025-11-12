# tests/test_checkin.py
from fastapi.testclient import TestClient
import pytest

from app.main import app, get_db  # import the FastAPI app and dependency to override


# Dummy DB object to satisfy the code that calls db.execute/db.commit
class DummyDB:
    def execute(self, *args, **kwargs):
        # return a simple object with fetchone if code expects it elsewhere
        class _R:
            def fetchone(self_inner):
                return None

            def mappings(self_inner):
                return []

            def all(self_inner):
                return []

        return _R()

    def commit(self):
        pass

    def close(self):
        pass


# override db
def override_get_db():
    db = DummyDB()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def override_db_dependency():
    # apply override
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


def test_create_checkin_with_dev_login():
    client = TestClient(app)

    # dev login endpoint to set the session cookie (dev auth enabled by default)
    # netid will be stored in session by the dev login handler.
    resp = client.get("/auth/dev/login?netid=testuser", follow_redirects=False)
    assert resp.status_code in (200, 302, 307, 308)

    # post to checkin
    r = client.post("/checkins", json={"venue_id": 42})
    assert r.status_code == 200
    data = r.json()
    assert data["venue_id"] == 42
    assert data["active"] is True
