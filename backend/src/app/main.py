from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy.orm import Session

from app.models import Venue as VenueModel
from app.schemas import CheckInCreate, CheckInResponse, VenueStatsResponse, VenueResponse
from app.database import get_db
from app.crud import checkins as crud_checkins
from app.crud import venues as crud_venues


# Pydantic model for in-memory venues (temporary, used by legacy endpoints)
class Venue(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    availability: float | None = None  # 0..1 (1 = very available)


app = FastAPI(title="SeatCheck API", version="0.1.0")

# DEV: open CORS so Expo/web can hit the API from localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


VENUES: list[Venue] = [
    Venue(id=1, name="Bass Library", lat=41.3083, lon=-72.9289, availability=0.7),
    Venue(
        id=2,
        name="Sterling Memorial Library",
        lat=41.3102,
        lon=-72.9276,
        availability=0.4,
    ),
]


class CheckIn(BaseModel):
    venue_id: int
    occupancy: int = Field(ge=0, le=3)  # 0=empty ... 3=packed
    noise: int = Field(ge=0, le=3)  # 0=quiet ... 3=loud


CHECKINS: list[dict[str, Any]] = []  # [{venue_id, occupancy, noise, ts}]


@app.post("/checkins")
def create_checkin(ci: CheckIn) -> dict[str, bool]:
    CHECKINS.append(
        {
            "venue_id": ci.venue_id,
            "occupancy": ci.occupancy,
            "noise": ci.noise,
            "ts": datetime.now(timezone.utc),
        }
    )
    _recompute_aggregates()
    return {"ok": True}


def _recompute_aggregates() -> None:
    # simple time-decayed average of availability = 1 - occupancy/3 (half-life 30 min)
    now = datetime.now(timezone.utc)
    half_life = timedelta(minutes=30)
    tau = half_life / 0.69314718056  # ln(2)
    by_venue: dict[int, list[tuple[float, float]]] = {}
    for row in CHECKINS:
        dt = (now - row["ts"]).total_seconds()
        w = pow(2.718281828, -(dt / tau.total_seconds()))
        av = 1.0 - (row["occupancy"] / 3.0)
        by_venue.setdefault(row["venue_id"], []).append((av, w))
    for v in VENUES:
        pairs = by_venue.get(v.id, [])
        if not pairs:
            continue
        num = sum(av * w for av, w in pairs)
        den = sum(w for _, w in pairs)
        v.availability = max(0.0, min(1.0, num / den))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


# ============================================================================
# Check-In Endpoints (API v1)
# ============================================================================


@app.post(
    "/api/v1/checkins",
    response_model=CheckInResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Check-Ins"],
)
def create_checkin(
    checkin: CheckInCreate,
    db: Session = Depends(get_db),
) -> CheckInResponse:
    """Create a new check-in for a venue.
    
    Records user-reported occupancy and noise levels for a specific venue.
    
    Args:
        checkin: Check-in data (venue_id, occupancy, noise)
        db: Database session (injected)
    
    Returns:
        Created check-in with ID and timestamp
    
    Raises:
        404: If venue doesn't exist
        422: If validation fails (occupancy/noise not in 0-5 range)
    """
    # TODO: Replace with real user authentication
    # For now, use a mock user_id
    mock_user_id = 1
    
    try:
        db_checkin = crud_checkins.create_checkin(
            db=db,
            checkin_data=checkin,
            user_id=mock_user_id,
        )
        return CheckInResponse.model_validate(db_checkin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@app.get(
    "/api/v1/venues/{venue_id}/stats",
    response_model=VenueStatsResponse,
    tags=["Venues"],
)
def get_venue_stats(
    venue_id: int,
    minutes: int = 2,
    db: Session = Depends(get_db),
) -> VenueStatsResponse:
    """Get aggregated statistics for a venue.
    
    Returns average occupancy and noise levels from recent check-ins.
    
    Args:
        venue_id: ID of the venue
        minutes: Time window in minutes (default: 2)
        db: Database session (injected)
    
    Returns:
        Venue statistics with averages and check-in count
    
    Raises:
        404: If venue doesn't exist
    """
    # Verify venue exists
    venue = db.query(VenueModel).filter(VenueModel.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venue with id {venue_id} not found",
        )
    
    # Get statistics
    stats = crud_checkins.get_venue_stats(db=db, venue_id=venue_id, minutes=minutes)
    
    return VenueStatsResponse(
        venue_id=venue_id,
        avg_occupancy=stats["avg_occupancy"],
        avg_noise=stats["avg_noise"],
        checkin_count=stats["checkin_count"],
        time_window_minutes=minutes,
        last_updated=datetime.now(timezone.utc),
    )


@app.get("/venues", response_model=list[Venue])
def list_venues() -> list[Venue]:
    return VENUES


@app.get("/venues.geojson")
def venues_geojson() -> JSONResponse:
    features = []
    for v in VENUES:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [v.lon, v.lat]},
                "properties": {
                    "id": v.id,
                    "name": v.name,
                    "availability": v.availability,
                },
            }
        )
    return JSONResponse({"type": "FeatureCollection", "features": features})


# =============================================================================
# PostGIS Spatial Query Endpoints
# =============================================================================


class NearbyVenueResponse(BaseModel):
    """Response model for nearby venues with distance."""
    venue: VenueResponse
    distance_meters: float = Field(..., description="Distance from query point in meters")
    
    model_config = {"from_attributes": True}


@app.get(
    "/api/v1/venues/nearby",
    response_model=list[NearbyVenueResponse],
    tags=["Venues", "Location"],
)
def get_nearby_venues(
    lat: float = Query(..., description="Latitude of center point", ge=-90, le=90),
    lon: float = Query(..., description="Longitude of center point", ge=-180, le=180),
    radius: float = Query(1000, description="Search radius in meters", gt=0, le=50000),
    limit: int = Query(20, description="Maximum number of results", gt=0, le=100),
    db: Session = Depends(get_db),
) -> list[NearbyVenueResponse]:
    """Find venues within a radius of a given location.
    
    Uses PostGIS spatial queries for efficient distance-based search.
    Results are ordered by distance from the query point.
    
    Args:
        lat: Latitude of center point (-90 to 90)
        lon: Longitude of center point (-180 to 180)
        radius: Search radius in meters (max: 50km)
        limit: Maximum number of results (max: 100)
        db: Database session (injected)
    
    Returns:
        List of venues with their distances from the query point
    
    Example:
        GET /api/v1/venues/nearby?lat=41.3083&lon=-72.9289&radius=500
    """
    results = crud_venues.get_nearby_venues(
        db=db,
        latitude=lat,
        longitude=lon,
        radius_meters=radius,
        limit=limit,
    )
    
    return [
        NearbyVenueResponse(
            venue=VenueResponse.model_validate(venue),
            distance_meters=distance
        )
        for venue, distance in results
    ]


@app.get(
    "/api/v1/venues/nearest",
    response_model=NearbyVenueResponse,
    tags=["Venues", "Location"],
)
def get_nearest_venue(
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    lon: float = Query(..., description="Longitude", ge=-180, le=180),
    db: Session = Depends(get_db),
) -> NearbyVenueResponse:
    """Find the nearest venue to a given location.
    
    Uses PostGIS spatial queries to find the single closest venue.
    
    Args:
        lat: Latitude of query point
        lon: Longitude of query point
        db: Database session (injected)
    
    Returns:
        Nearest venue with distance in meters
    
    Raises:
        404: If no venues exist in database
    
    Example:
        GET /api/v1/venues/nearest?lat=41.3083&lon=-72.9289
    """
    result = crud_venues.get_nearest_venue(db=db, latitude=lat, longitude=lon)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No venues found in database",
        )
    
    venue, distance = result
    return NearbyVenueResponse(
        venue=VenueResponse.model_validate(venue),
        distance_meters=distance
    )


@app.get(
    "/api/v1/venues/in-bounds",
    response_model=list[VenueResponse],
    tags=["Venues", "Location"],
)
def get_venues_in_bounds(
    min_lat: float = Query(..., description="Minimum latitude (south)", ge=-90, le=90),
    max_lat: float = Query(..., description="Maximum latitude (north)", ge=-90, le=90),
    min_lon: float = Query(..., description="Minimum longitude (west)", ge=-180, le=180),
    max_lon: float = Query(..., description="Maximum longitude (east)", ge=-180, le=180),
    db: Session = Depends(get_db),
) -> list[VenueResponse]:
    """Get all venues within a bounding box.
    
    Useful for retrieving venues visible in a map viewport.
    Uses PostGIS spatial index for efficient queries.
    
    Args:
        min_lat: Minimum latitude (southern bound)
        max_lat: Maximum latitude (northern bound)
        min_lon: Minimum longitude (western bound)
        max_lon: Maximum longitude (eastern bound)
        db: Database session (injected)
    
    Returns:
        List of venues within the bounding box
    
    Example:
        GET /api/v1/venues/in-bounds?min_lat=41.30&max_lat=41.32&min_lon=-72.94&max_lon=-72.92
    """
    if min_lat >= max_lat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_lat must be less than max_lat",
        )
    if min_lon >= max_lon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_lon must be less than max_lon",
        )
    
    venues = crud_venues.get_venues_in_bounding_box(
        db=db,
        min_lat=min_lat,
        max_lat=max_lat,
        min_lon=min_lon,
        max_lon=max_lon,
    )
    
    return [VenueResponse.model_validate(venue) for venue in venues]


@app.get(
    "/api/v1/venues/{venue_id}",
    response_model=VenueResponse,
    tags=["Venues"],
)
def get_venue_by_id(
    venue_id: int,
    db: Session = Depends(get_db),
) -> VenueResponse:
    """Get a specific venue by ID.
    
    Args:
        venue_id: ID of the venue
        db: Database session (injected)
    
    Returns:
        Venue details
    
    Raises:
        404: If venue doesn't exist
    """
    venue = crud_venues.get_venue_by_id(db=db, venue_id=venue_id)
    
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venue with id {venue_id} not found",
        )
    
    return VenueResponse.model_validate(venue)


@app.get(
    "/api/v1/venues",
    response_model=list[VenueResponse],
    tags=["Venues"],
)
def get_all_venues(
    skip: int = Query(0, description="Number of records to skip", ge=0),
    limit: int = Query(100, description="Maximum number of records", ge=1, le=1000),
    db: Session = Depends(get_db),
) -> list[VenueResponse]:
    """Get all venues with pagination.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        db: Database session (injected)
    
    Returns:
        List of venues
    """
    venues = crud_venues.get_all_venues(db=db, skip=skip, limit=limit)
    return [VenueResponse.model_validate(venue) for venue in venues]


# =============================================================================
# Legacy Endpoints (for backward compatibility)
# =============================================================================


# Simple desktop map at /map using Leaflet
@app.get("/map", response_class=HTMLResponse)
def web_map() -> HTMLResponse:
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
