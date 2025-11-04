def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "time" in data


def test_list_venues(client):
    r = client.get(
        "/auth/dev/login", params={"netid": "testuser"}, follow_redirects=False
    )
    assert r.status_code in (200, 302)
    r2 = client.get("/venues/with_occupancy")
    assert r2.status_code == 200
