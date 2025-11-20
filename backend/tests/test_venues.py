"""Test cases for venue-related endpoints."""


def test_list_venues_authenticated(authenticated_client):
    """Test listing all venues when authenticated."""
    response = authenticated_client.get("/venues")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Check structure of venue objects
    if len(data) > 0:
        venue = data[0]
        assert "id" in venue
        assert "name" in venue
        assert "lat" in venue
        assert "lon" in venue
        assert "capacity" in venue


def test_list_venues_unauthenticated(client):
    """Test that listing venues requires authentication."""
    from fastapi.testclient import TestClient
    from app.main import app

    fresh_client = TestClient(app)

    response = fresh_client.get("/venues")
    assert response.status_code == 401


def test_venues_with_occupancy_default_window(authenticated_client):
    """Test venues with occupancy using default time window."""
    response = authenticated_client.get("/venues/with_occupancy")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Check structure includes occupancy metrics
    if len(data) > 0:
        venue = data[0]
        assert "id" in venue
        assert "name" in venue
        assert "lat" in venue
        assert "lon" in venue
        assert "capacity" in venue
        assert "availability" in venue
        assert "avg_occupancy" in venue
        assert "avg_noise" in venue
        assert "recent_count" in venue


def test_venues_with_occupancy_custom_window(authenticated_client):
    """Test venues with occupancy using custom time window."""
    response = authenticated_client.get("/venues/with_occupancy", params={"window": 60})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_venues_with_occupancy_invalid_window(authenticated_client):
    """Test venues with occupancy using invalid time window."""
    response = authenticated_client.get(
        "/venues/with_occupancy", params={"window": "invalid"}
    )
    assert response.status_code == 422  # Validation error


def test_venues_with_occupancy_zero_window(authenticated_client):
    """Test venues with occupancy using zero time window."""
    response = authenticated_client.get("/venues/with_occupancy", params={"window": 0})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_venues_with_occupancy_large_window(authenticated_client):
    """Test venues with occupancy using large time window."""
    response = authenticated_client.get(
        "/venues/with_occupancy", params={"window": 1440}
    )  # 24 hours
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_venues_geojson(authenticated_client):
    """Test GeoJSON format venue listing."""
    response = authenticated_client.get("/venues.geojson")
    assert response.status_code == 200
    data = response.json()

    # Verify GeoJSON structure
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert isinstance(data["features"], list)

    # Check feature structure
    if len(data["features"]) > 0:
        feature = data["features"][0]
        assert feature["type"] == "Feature"
        assert "geometry" in feature
        assert feature["geometry"]["type"] == "Point"
        assert "coordinates" in feature["geometry"]
        assert len(feature["geometry"]["coordinates"]) == 2  # [lon, lat]
        assert "properties" in feature
        assert "name" in feature["properties"]
        assert "capacity" in feature["properties"]


def test_venues_geojson_unauthenticated(client):
    """Test that GeoJSON endpoint requires authentication."""
    from fastapi.testclient import TestClient
    from app.main import app

    fresh_client = TestClient(app)

    response = fresh_client.get("/venues.geojson")
    assert response.status_code == 401


def test_venue_stats_by_id(authenticated_client):
    """Test getting stats for a specific venue."""
    # First get a venue ID
    venues_response = authenticated_client.get("/venues")
    venues = venues_response.json()

    if len(venues) > 0:
        venue_id = venues[0]["id"]

        response = authenticated_client.get(f"/api/v1/venues/{venue_id}/stats")
        assert response.status_code == 200
        data = response.json()

        assert data["venue_id"] == venue_id
        assert "name" in data
        assert "lat" in data
        assert "lon" in data
        assert "capacity" in data
        assert "availability" in data
        assert "avg_occupancy" in data
        assert "avg_noise" in data
        assert "recent_count" in data


def test_venue_stats_custom_window(authenticated_client):
    """Test getting venue stats with custom time window."""
    venues_response = authenticated_client.get("/venues")
    venues = venues_response.json()

    if len(venues) > 0:
        venue_id = venues[0]["id"]

        response = authenticated_client.get(
            f"/api/v1/venues/{venue_id}/stats", params={"minutes": 60}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["venue_id"] == venue_id


def test_venue_stats_nonexistent_venue(authenticated_client):
    """Test getting stats for non-existent venue."""
    response = authenticated_client.get("/api/v1/venues/99999/stats")
    # API returns 200 with stats even for nonexistent venues (returns 0/None values)
    # Venue existence validation would require additional query
    assert response.status_code == 200
    data = response.json()
    assert data["venue_id"] == 99999
    # Stats will be None/0 for nonexistent venue
    assert "avg_occupancy" in data
    assert "avg_noise" in data


def test_venue_stats_invalid_venue_id(authenticated_client):
    """Test getting stats with invalid venue ID."""
    response = authenticated_client.get("/api/v1/venues/invalid/stats")
    assert response.status_code == 422  # Validation error


def test_venue_stats_unauthenticated(client):
    """Test that venue stats require authentication."""
    from fastapi.testclient import TestClient
    from app.main import app

    fresh_client = TestClient(app)

    response = fresh_client.get("/api/v1/venues/1/stats")
    assert response.status_code == 401


def test_venues_data_consistency(authenticated_client):
    """Test that venue data is consistent across endpoints."""
    # Get venues from basic endpoint
    venues_response = authenticated_client.get("/venues")
    venues = venues_response.json()

    # Get venues with occupancy
    occupancy_response = authenticated_client.get("/venues/with_occupancy")
    venues_with_occupancy = occupancy_response.json()

    # Get GeoJSON
    geojson_response = authenticated_client.get("/venues.geojson")
    geojson = geojson_response.json()

    # Should have same number of venues
    assert len(venues) == len(venues_with_occupancy)
    assert len(venues) == len(geojson["features"])

    # Check that all venue IDs match
    venue_ids = {v["id"] for v in venues}
    occupancy_ids = {v["id"] for v in venues_with_occupancy}
    geojson_ids = {f["properties"]["id"] for f in geojson["features"]}

    assert venue_ids == occupancy_ids
    assert venue_ids == geojson_ids


def test_venues_capacity_values(authenticated_client):
    """Test that venue capacity values are reasonable."""
    response = authenticated_client.get("/venues")
    venues = response.json()

    for venue in venues:
        assert venue["capacity"] > 0, f"Venue {venue['name']} has invalid capacity"
        assert venue["capacity"] <= 10000, (
            f"Venue {venue['name']} has unrealistic capacity"
        )


def test_venues_coordinates_valid(authenticated_client):
    """Test that venue coordinates are valid."""
    response = authenticated_client.get("/venues")
    venues = response.json()

    for venue in venues:
        # Check latitude is valid (-90 to 90)
        assert -90 <= venue["lat"] <= 90, f"Venue {venue['name']} has invalid latitude"

        # Check longitude is valid (-180 to 180)
        assert -180 <= venue["lon"] <= 180, (
            f"Venue {venue['name']} has invalid longitude"
        )


def test_venues_geojson_coordinates_order(authenticated_client):
    """Test that GeoJSON coordinates are in [lon, lat] order."""
    response = authenticated_client.get("/venues.geojson")
    geojson = response.json()

    for feature in geojson["features"]:
        coords = feature["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]

        # GeoJSON uses [lon, lat] order
        assert -180 <= lon <= 180, "First coordinate should be longitude"
        assert -90 <= lat <= 90, "Second coordinate should be latitude"


def test_venues_occupancy_metrics_bounds(authenticated_client):
    """Test that occupancy metrics are within valid bounds."""
    response = authenticated_client.get("/venues/with_occupancy")
    venues = response.json()

    for venue in venues:
        # Availability should be 0-1
        if venue["availability"] is not None:
            assert 0 <= venue["availability"] <= 1, (
                f"Venue {venue['name']} has invalid availability"
            )

        # Average occupancy should be 0-5 (or null)
        if venue["avg_occupancy"] is not None:
            assert 0 <= venue["avg_occupancy"] <= 5, (
                f"Venue {venue['name']} has invalid avg_occupancy"
            )

        # Average noise should be 0-5 (or null)
        if venue["avg_noise"] is not None:
            assert 0 <= venue["avg_noise"] <= 5, (
                f"Venue {venue['name']} has invalid avg_noise"
            )

        # Recent count should be non-negative
        if venue["recent_count"] is not None:
            assert venue["recent_count"] >= 0, (
                f"Venue {venue['name']} has negative recent_count"
            )
