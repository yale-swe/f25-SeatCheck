"""Venue endpoints for location data and heatmaps."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Venue
from app.schemas.location import Venue as VenueResponse
from app.schemas.venue import VenueStatus
from app.services.metrics import compute_venue_metrics

router = APIRouter()


@router.get("", response_model=list[VenueResponse])
def list_venues(db: Session = Depends(get_db)) -> list[VenueResponse]:
    """List all venues with computed availability scores.

    Returns all venues with their current availability based on recent check-ins
    using time-decayed aggregation.

    Args:
        db: Database session

    Returns:
        List of venues with availability scores
    """
    venues = db.query(Venue).all()

    result = []
    for venue in venues:
        metrics = compute_venue_metrics(venue.id, db)
        result.append(
            VenueResponse(
                id=venue.id,
                name=venue.name,
                lat=venue.lat,
                lon=venue.lon,
                availability=metrics["availability"],
            )
        )

    return result


@router.get("/{venue_id}/status", response_model=VenueStatus)
def get_venue_status(venue_id: int, db: Session = Depends(get_db)) -> VenueStatus:
    """Get current status and availability metrics for a specific venue.

    Returns time-decayed averages of occupancy, noise, and computed availability score.
    This endpoint is useful for detailed heatmap data and real-time status updates.

    Args:
        venue_id: ID of the venue
        db: Database session

    Returns:
        Detailed venue status with heatmap metrics

    Raises:
        HTTPException: 404 if venue not found
    """
    # Verify venue exists
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail=f"Venue {venue_id} not found")

    # Compute metrics
    metrics = compute_venue_metrics(venue_id, db)

    return VenueStatus(
        venue_id=venue_id,
        venue_name=venue.name,
        availability=metrics["availability"],
        avg_occupancy=metrics["avg_occupancy"],
        avg_noise=metrics["avg_noise"],
        recent_checkins_count=metrics["recent_count"],
        last_updated=metrics["last_updated"],
    )


@router.get(".geojson")
def venues_geojson(db: Session = Depends(get_db)) -> JSONResponse:
    """Get all venues as a GeoJSON FeatureCollection.

    Useful for mapping applications and geospatial visualization.
    Includes availability, occupancy, and noise metrics for each venue.

    Args:
        db: Database session

    Returns:
        GeoJSON FeatureCollection with venue data
    """
    venues = db.query(Venue).all()

    features = []
    for venue in venues:
        metrics = compute_venue_metrics(venue.id, db)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [venue.lon, venue.lat]},
                "properties": {
                    "id": venue.id,
                    "name": venue.name,
                    "availability": metrics["availability"],
                    "avg_occupancy": metrics["avg_occupancy"],
                    "avg_noise": metrics["avg_noise"],
                },
            }
        )

    return JSONResponse({"type": "FeatureCollection", "features": features})


@router.get("/map", response_class=HTMLResponse)
def web_map() -> HTMLResponse:
    """Simple desktop map viewer using Leaflet.js.

    Provides an interactive web-based map showing all venues with color-coded
    availability markers:
    - Green (>66%): High availability
    - Yellow (33-66%): Moderate availability
    - Red (<33%): Low availability

    Returns:
        HTML page with interactive map
    """
    html = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>SeatCheck Map (Desktop MVP)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""
  />
  <style>html, body, #map { height: 100%; margin: 0; }</style>
</head>
<body>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
    crossorigin=""></script>
  <script>
    const YALE = [41.3083, -72.9279];
    const map = L.map('map').setView(YALE, 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    fetch('/venues.geojson')
      .then(r => r.json())
      .then(fc => {
        fc.features.forEach(f => {
          const [lon, lat] = f.geometry.coordinates;
          const name = f.properties.name;
          const avail = f.properties.availability ?? 0.5;
          // simple availability-to-color (more available = greener)
          const color = avail >= 0.66 ? '#2ecc71' : (avail >= 0.33 ? '#f1c40f' : '#e74c3c');

          L.circleMarker([lat, lon], {
            radius: 10,
            color: color,
            fillColor: color,
            fillOpacity: 0.7,
            weight: 2
          })
          .bindPopup(`<b>${name}</b><br/>Availability: ${(avail*100)|0}%`)
          .addTo(map);
        });
      })
      .catch(err => console.error('Failed to load venues:', err));
  </script>
</body>
</html>
"""
    return HTMLResponse(html)
