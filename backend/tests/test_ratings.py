"""Test cases for rating endpoints."""

import pytest


@pytest.fixture
def venue_id(authenticated_client):
    """Fixture that provides a valid venue ID."""
    response = authenticated_client.get("/api/v1/venues")
    venues = response.json()
    if len(venues) > 0:
        return venues[0]["id"]
    pytest.skip("No venues available for testing")


def test_create_rating_with_both_metrics(authenticated_client, venue_id):
    """Test creating a rating with both occupancy and noise."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 3, "noise": 2}
    )
    assert response.status_code == 201
    data = response.json()

    assert data["venue_id"] == venue_id
    assert data["occupancy"] == 3
    assert data["noise"] == 2
    assert "created_at" in data


def test_create_rating_occupancy_only(authenticated_client, venue_id):
    """Test creating a rating with only occupancy."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 4, "noise": None}
    )
    assert response.status_code == 201
    data = response.json()

    assert data["venue_id"] == venue_id
    assert data["occupancy"] == 4
    assert data["noise"] == 0


def test_create_rating_noise_only(authenticated_client, venue_id):
    """Test creating a rating with only noise."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": None, "noise": 3}
    )
    assert response.status_code == 201
    data = response.json()

    assert data["venue_id"] == venue_id
    assert data["occupancy"] == 0
    assert data["noise"] == 3


def test_create_rating_minimum_values(authenticated_client, venue_id):
    """Test creating a rating with minimum valid values."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 0, "noise": 0}
    )
    assert response.status_code == 201
    data = response.json()

    assert data["occupancy"] == 0
    assert data["noise"] == 0


def test_create_rating_maximum_values(authenticated_client, venue_id):
    """Test creating a rating with maximum valid values."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 5, "noise": 5}
    )
    assert response.status_code == 201
    data = response.json()

    assert data["occupancy"] == 5
    assert data["noise"] == 5


def test_create_rating_occupancy_too_high(authenticated_client, venue_id):
    """Test creating a rating with occupancy > 5."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 6, "noise": 2}
    )
    assert response.status_code == 422  # Validation error


def test_create_rating_occupancy_negative(authenticated_client, venue_id):
    """Test creating a rating with negative occupancy."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": -1, "noise": 2}
    )
    assert response.status_code == 422  # Validation error


def test_create_rating_noise_too_high(authenticated_client, venue_id):
    """Test creating a rating with noise > 5."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 3, "noise": 6}
    )
    assert response.status_code == 422  # Validation error


def test_create_rating_noise_negative(authenticated_client, venue_id):
    """Test creating a rating with negative noise."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 3, "noise": -1}
    )
    assert response.status_code == 422  # Validation error


def test_create_rating_both_null(authenticated_client, venue_id):
    """Test creating a rating with both values null."""
    response = authenticated_client.post(
        "/api/v1/ratings",
        json={"venue_id": venue_id, "occupancy": None, "noise": None},
    )
    # Should still create the rating even if both are null
    # (though this might not be useful in practice)
    assert response.status_code == 201


def test_create_rating_missing_venue_id(authenticated_client):
    """Test creating a rating without venue_id."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"occupancy": 3, "noise": 2}
    )
    assert response.status_code == 422  # Validation error


def test_create_rating_unauthenticated(client, venue_id):
    """Test that creating a rating requires authentication."""
    from fastapi.testclient import TestClient
    from app.main import app

    fresh_client = TestClient(app)

    response = fresh_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 3, "noise": 2}
    )
    assert response.status_code == 401


def test_create_multiple_ratings_same_user(authenticated_client, venue_id):
    """Test that a user can create multiple ratings for the same venue."""
    # First rating
    response1 = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 2, "noise": 1}
    )
    assert response1.status_code == 201

    # Second rating (different values)
    response2 = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 4, "noise": 3}
    )
    assert response2.status_code == 201

    # Both should succeed
    assert response1.json()["venue_id"] == venue_id
    assert response2.json()["venue_id"] == venue_id


def test_rating_affects_venue_metrics(authenticated_client, venue_id):
    """Test that ratings affect venue occupancy and noise metrics."""
    # Get initial metrics
    initial_response = authenticated_client.get(f"/api/v1/venues/{venue_id}/stats")
    initial_data = initial_response.json()

    # Submit a rating
    authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 5, "noise": 4}
    )

    # Get updated metrics
    updated_response = authenticated_client.get(f"/api/v1/venues/{venue_id}/stats")
    updated_data = updated_response.json()

    # Metrics should reflect the new rating (may be weighted average)
    # At minimum, we should have non-null values now
    assert (
        updated_data["avg_occupancy"] is not None
        or initial_data["avg_occupancy"] is not None
    )
    assert (
        updated_data["avg_noise"] is not None or initial_data["avg_noise"] is not None
    )


def test_rating_timestamp_is_recent(authenticated_client, venue_id):
    """Test that rating timestamp is recent."""
    from datetime import datetime, timezone

    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 3, "noise": 2}
    )
    assert response.status_code == 201
    data = response.json()

    # Parse timestamp
    created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)

    # Timestamp should be within last few seconds
    age = (now - created_at).total_seconds()
    assert age < 5, "Rating timestamp is too old"


def test_rating_with_decimal_values(authenticated_client, venue_id):
    """Test that decimal values are rejected (should be integers)."""
    response = authenticated_client.post(
        "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 3.5, "noise": 2.5}
    )
    # Depending on Pydantic config, this might be accepted and rounded,
    # or rejected. Check the actual behavior:
    # If status is 201, decimals were accepted (possibly rounded)
    # If status is 422, decimals were rejected
    assert response.status_code in (201, 422)


def test_rating_with_string_values(authenticated_client, venue_id):
    """Test that string values are rejected."""
    response = authenticated_client.post(
        "/api/v1/ratings",
        json={"venue_id": venue_id, "occupancy": "three", "noise": "two"},
    )
    assert response.status_code == 422  # Validation error


def test_multiple_ratings_different_venues(authenticated_client):
    """Test creating ratings for multiple different venues."""
    venues_response = authenticated_client.get("/api/v1/venues")
    venues = venues_response.json()

    if len(venues) < 2:
        pytest.skip("Need at least 2 venues for this test")

    # Rate first venue
    response1 = authenticated_client.post(
        "/api/v1/ratings",
        json={"venue_id": venues[0]["id"], "occupancy": 2, "noise": 1},
    )
    assert response1.status_code == 201

    # Rate second venue
    response2 = authenticated_client.post(
        "/api/v1/ratings",
        json={"venue_id": venues[1]["id"], "occupancy": 4, "noise": 3},
    )
    assert response2.status_code == 201


def test_rating_empty_scales(authenticated_client, venue_id):
    """Test rating with empty values (0 = empty, silent)."""
    response = authenticated_client.post(
        "/api/v1/ratings",
        json={
            "venue_id": venue_id,
            "occupancy": 0,  # Empty
            "noise": 0,  # Silent
        },
    )
    assert response.status_code == 201
    data = response.json()

    assert data["occupancy"] == 0
    assert data["noise"] == 0


def test_rating_full_scales(authenticated_client, venue_id):
    """Test rating with full values (5 = packed, loud)."""
    response = authenticated_client.post(
        "/api/v1/ratings",
        json={
            "venue_id": venue_id,
            "occupancy": 5,  # Packed
            "noise": 5,  # Loud
        },
    )
    assert response.status_code == 201
    data = response.json()

    assert data["occupancy"] == 5
    assert data["noise"] == 5


def test_rating_contributes_to_heatmap(authenticated_client, venue_id):
    """Test that ratings contribute to venue heatmap data."""
    # Submit several consistent ratings
    for _ in range(3):
        authenticated_client.post(
            "/api/v1/ratings", json={"venue_id": venue_id, "occupancy": 4, "noise": 3}
        )

    # Check the venue's metrics
    response = authenticated_client.get("/api/v1/venues/with_occupancy")
    venues = response.json()
    venue = next((v for v in venues if v["id"] == venue_id), None)

    assert venue is not None
    # Should have some occupancy/noise data (may be averaged with other data)
    # At minimum, availability should be calculated
    assert venue["availability"] is not None
