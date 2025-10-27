from fastapi.testclient import TestClient
import httpx

from app.main import app


def test_redirects_to_cas_login():
    """when no ticket is present, the /cas route should redirect to the CAS login URL."""
    client = TestClient(app)
    resp = client.get("/cas", follow_redirects=False)
    assert resp.status_code in (302, 307)
    loc = resp.headers.get("location", "")
    # should point at the configured CAS login route and include the service param
    assert "login" in loc.lower()
    assert "service=" in loc


def test_cas_callback_sets_session(monkeypatch):
    """simulate CAS validation response and assert session user is set.

    We monkeypatch httpx.AsyncClient.get to return a fake response containing
    a CAS authenticationSuccess block with a <cas:user>netid</cas:user>.
    """

    async def fake_get(self, url, params=None):
        class FakeResponse:
            text = (
                "<cas:serviceResponse>"
                "<authenticationSuccess>"
                "<cas:user>netid123</cas:user>"
                "</authenticationSuccess>"
                "</cas:serviceResponse>"
            )

        return FakeResponse()

    # patch the AsyncClient.get method used by the CAS handler
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    client = TestClient(app)

    # call the CAS callback with a ticket (don't follow redirect so we can assert location)
    resp = client.get("/cas?ticket=FAKE_TICKET", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "/check" in resp.headers.get("location", "")

    # now call /check with the same client (cookie is preserved) to verify session
    resp2 = client.get("/check")
    assert resp2.status_code == 200
    body = resp2.json()
    assert body.get("auth") is True
    assert body.get("user", {}).get("netid") == "netid123"
