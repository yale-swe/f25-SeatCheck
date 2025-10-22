from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, timezone, timedelta
from typing import Any


app = FastAPI(title="SeatCheck API", version="0.1.0")

# DEV: open CORS so Expo/web can hit the API from localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Venue(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    availability: float | None = None  # 0..1 (1 = very available)


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
