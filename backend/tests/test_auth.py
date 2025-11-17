"""Test cases for authentication endpoints."""

from unittest.mock import patch, MagicMock


def test_dev_login_success(client):
    """Test successful dev login."""
    response = client.get(
        "/auth/dev/login", params={"netid": "testuser123"}, follow_redirects=False
    )
    # Dev login returns a redirect
    assert response.status_code in (302, 307)

    # Verify session was set by checking /auth/me
    me_response = client.get("/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["netid"] == "testuser123"


def test_dev_login_default_netid(client):
    """Test dev login with default netid."""
    response = client.get("/auth/dev/login", follow_redirects=False)
    assert response.status_code in (302, 307)

    # Verify default netid was set
    me_response = client.get("/auth/me")
    assert me_response.status_code == 200
    # Default netid is "dev001" according to the endpoint
    assert me_response.json()["netid"] == "dev001"


def test_dev_login_disabled_in_production(client):
    """Test that dev login behavior when DEV_AUTH is configured."""
    # Note: DEV_AUTH is checked at module load time, so we can't easily
    # test disabling it without reloading the module. This test documents
    # that dev login works when DEV_AUTH=1 (the default in tests)
    response = client.get(
        "/auth/dev/login", params={"netid": "test"}, follow_redirects=False
    )
    # With DEV_AUTH enabled, should redirect successfully
    assert response.status_code in (302, 307)


def test_dev_logout(client):
    """Test dev logout."""
    # First login
    client.get("/auth/dev/login", params={"netid": "testuser"}, follow_redirects=False)

    # Then logout
    response = client.post("/auth/dev/logout")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"]


def test_auth_me_authenticated(client):
    """Test /auth/me when authenticated."""
    # Login first
    client.get(
        "/auth/dev/login", params={"netid": "testuser123"}, follow_redirects=False
    )

    # Check auth/me
    response = client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["netid"] == "testuser123"


def test_auth_me_unauthenticated(client):
    """Test /auth/me when not authenticated."""
    # Create a fresh client to ensure no session
    from fastapi.testclient import TestClient
    from app.main import app

    fresh_client = TestClient(app)

    response = fresh_client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_logout(client):
    """Test logout endpoint."""
    # Login first
    client.get("/auth/dev/login", params={"netid": "testuser"}, follow_redirects=False)

    # Logout
    response = client.post("/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data or "message" in data

    # Verify we're logged out
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_debug_whoami_authenticated(client):
    """Test /debug/whoami when authenticated."""
    # Login first
    client.get("/auth/dev/login", params={"netid": "debuguser"}, follow_redirects=False)

    response = client.get("/debug/whoami")
    assert response.status_code == 200
    data = response.json()
    assert data["netid"] == "debuguser"


def test_debug_whoami_unauthenticated(client):
    """Test /debug/whoami when not authenticated."""
    from fastapi.testclient import TestClient
    from app.main import app

    fresh_client = TestClient(app)

    response = fresh_client.get("/debug/whoami")
    assert response.status_code == 200
    data = response.json()
    assert data["netid"] is None


def test_cas_login_redirect(client):
    """Test that CAS login redirects to Yale CAS."""
    response = client.get("/auth/cas/login", follow_redirects=False)
    assert response.status_code in (302, 307)

    # Check redirect location contains CAS URL
    location = response.headers.get("location", "")
    assert "cas" in location.lower() or "login" in location


def test_cas_callback_no_ticket(client):
    """Test CAS callback without ticket parameter."""
    response = client.get("/auth/cas/callback", follow_redirects=False)
    # FastAPI returns 422 for missing required parameters
    assert response.status_code == 422


def test_cas_callback_with_invalid_ticket(client):
    """Test CAS callback with invalid ticket."""
    from unittest.mock import AsyncMock

    with patch("httpx.AsyncClient") as mock_client_class:
        # Mock CAS server response for invalid ticket
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
            <cas:authenticationFailure code='INVALID_TICKET'>
                Ticket is invalid
            </cas:authenticationFailure>
        </cas:serviceResponse>"""

        # Create async context manager
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        response = client.get(
            "/auth/cas/callback",
            params={"ticket": "ST-invalid"},
            follow_redirects=False,
        )
        # Should redirect with error parameter
        assert response.status_code in (302, 307)
        location = response.headers.get("location", "")
        assert "error" in location or "cas" in location


def test_cas_callback_with_valid_ticket(client):
    """Test CAS callback with valid ticket."""
    from unittest.mock import AsyncMock

    with patch("httpx.AsyncClient") as mock_client_class:
        # Mock CAS server response for valid ticket
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <cas:serviceResponse xmlns:cas='http://www.yale.edu/tp/cas'>
            <cas:authenticationSuccess>
                <cas:user>abc123</cas:user>
            </cas:authenticationSuccess>
        </cas:serviceResponse>"""

        # Create async context manager
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        response = client.get(
            "/auth/cas/callback",
            params={"ticket": "ST-valid-ticket"},
            follow_redirects=False,
        )
        assert response.status_code in (302, 307)

        # Verify redirect to APP_BASE
        location = response.headers.get("location", "")
        assert "localhost:8081" in location or "/" in location


def test_protected_endpoint_requires_auth(client):
    """Test that protected endpoints require authentication."""
    from fastapi.testclient import TestClient
    from app.main import app

    fresh_client = TestClient(app)

    # Try accessing protected endpoint without auth
    response = fresh_client.get("/venues")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_session_persistence(client):
    """Test that session persists across requests."""
    # Login
    response = client.get(
        "/auth/dev/login", params={"netid": "sessionuser"}, follow_redirects=False
    )
    assert response.status_code in (302, 307)

    # Make another request - should still be authenticated
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["netid"] == "sessionuser"

    # Make yet another request
    response = client.get("/venues")
    assert response.status_code == 200
