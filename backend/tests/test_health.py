def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "time" in data

def test_list_venues(client):
    r = client.get("/venues")
    assert r.status_code == 200
    venues = r.json()
    assert isinstance(venues, list)
    assert any(v["name"].startswith("Bass") for v in venues)
