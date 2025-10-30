# backend/src/app/main.py
from __future__ import annotations

import os
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------
app = FastAPI(title="SeatCheck API", version="0.1.0")

# ---- Frontend base ----------------------------------------------------------
APP_BASE = os.getenv("APP_BASE", "http://localhost:8081")

# ---- CORS -------------------------------------------------------------------
DEV_ORIGINS = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---- Session cookies --------------------------------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-insecure-change-me"),
    session_cookie="seatcheck_session",
    same_site="lax",
    https_only=False,  # True in prod behind HTTPS
    max_age=60 * 60 * 24 * 7,  # 7 days
)

# -----------------------------------------------------------------------------
# CAS configuration
# -----------------------------------------------------------------------------
CAS_BASE = os.getenv("CAS_BASE", "https://secure.its.yale.edu/cas")
SERVICE_PATH = "/auth/cas/callback"

def service_url(request: Request) -> str:
    host = request.headers.get("host", "localhost:8000")
    scheme = "https" if request.url.scheme == "https" else "http"
    return f"{scheme}://{host}{SERVICE_PATH}"

# -----------------------------------------------------------------------------
# Models & dummy data
# -----------------------------------------------------------------------------
class Venue(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    availability: float | None = None

VENUES: List[Venue] = [
    Venue(id=1, name="Bass Library", lat=41.3083, lon=-72.9289),
    Venue(id=2, name="Sterling Memorial Library", lat=41.3102, lon=-72.9276),
]

class CheckIn(BaseModel):
    venue_id: int
    occupancy: int = Field(ge=0, le=3)

CHECKINS: List[Dict[str, object]] = []

# -----------------------------------------------------------------------------
# Auth helpers
# -----------------------------------------------------------------------------
def require_login(request: Request) -> str:
    netid = request.session.get("netid")
    if not netid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return str(netid)

# -----------------------------------------------------------------------------
# Root redirect
# -----------------------------------------------------------------------------
@app.get("/")
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url=f"{APP_BASE}/", status_code=302)

# -----------------------------------------------------------------------------
# CAS routes
# -----------------------------------------------------------------------------
@app.get("/auth/cas/login")
def cas_login(request: Request) -> RedirectResponse:
    svc = urllib.parse.quote(service_url(request), safe="")
    return RedirectResponse(f"{CAS_BASE}/login?service={svc}", status_code=302)

@app.get(SERVICE_PATH)
async def cas_callback(request: Request, ticket: str) -> RedirectResponse:
    svc = urllib.parse.quote(service_url(request), safe="")
    validate_url = (
        f"{CAS_BASE}/p3/serviceValidate?service={svc}"
        f"&ticket={urllib.parse.quote(ticket, safe='')}"
    )

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(validate_url)

    print("[CAS RAW]", resp.text[:400])

    if resp.status_code != 200:
        return RedirectResponse(url=f"{APP_BASE}/login?error=cas_http", status_code=302)

    ns = {"cas": "http://www.yale.edu/tp/cas"}
    try:
        root = ET.fromstring(resp.text)
        user_el = root.find(".//cas:authenticationSuccess/cas:user", ns)
        netid = (user_el.text or "").strip() if user_el is not None else ""
    except ET.ParseError:
        netid = ""

    print("[CAS CALLBACK]", "netid=", netid)

    if not netid:
        return RedirectResponse(url=f"{APP_BASE}/login?error=cas_failed", status_code=302)

    request.session["netid"] = netid
    return RedirectResponse(url=f"{APP_BASE}/", status_code=302)

# -----------------------------------------------------------------------------
# Dev-only login (no CAS)
# -----------------------------------------------------------------------------
DEV_AUTH = os.getenv("DEV_AUTH", "1") == "1"

@app.get("/auth/dev/login")
def dev_login(request: Request, netid: str = "dev001"):
    """Temporary dev-only login to simulate CAS for testing."""
    if not DEV_AUTH:
        raise HTTPException(status_code=404, detail="Disabled")
    request.session["netid"] = netid
    print(f"[DEV LOGIN] netid={netid}")
    return RedirectResponse(url=f"{APP_BASE}/", status_code=status.HTTP_302_FOUND)

@app.post("/auth/dev/logout")
def dev_logout(request: Request):
    if not DEV_AUTH:
        raise HTTPException(status_code=404, detail="Disabled")
    request.session.clear()
    print("[DEV LOGOUT]")
    return {"ok": True}

# -----------------------------------------------------------------------------
# Debug helper
# -----------------------------------------------------------------------------
@app.get("/debug/whoami")
def whoami(request: Request):
    return {"netid": request.session.get("netid")}

# -----------------------------------------------------------------------------
# Auth endpoints
# -----------------------------------------------------------------------------
@app.get("/auth/me")
def me(request: Request) -> Dict[str, str]:
    netid = request.session.get("netid")
    if not netid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"netid": netid}

@app.post("/auth/logout")
def logout(request: Request) -> Dict[str, bool]:
    request.session.clear()
    return {"ok": True}

# -----------------------------------------------------------------------------
# Protected app API
# -----------------------------------------------------------------------------
@app.get("/venues", response_model=List[Venue])
def list_venues(_: str = Depends(require_login)) -> List[Venue]:
    return VENUES

@app.get("/venues.geojson")
def venues_geojson(_: str = Depends(require_login)) -> JSONResponse:
    features: List[Dict[str, object]] = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [v.lon, v.lat]},
            "properties": {"id": v.id, "name": v.name, "availability": v.availability},
        }
        for v in VENUES
    ]
    return JSONResponse({"type": "FeatureCollection", "features": features})

@app.get("/checkins")
def get_checkins(window: int = 120, _: str = Depends(require_login)) -> List[Dict[str, int]]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=window)
    counts: Dict[int, int] = {v.id: 0 for v in VENUES}
    for row in CHECKINS:
        ts = row.get("ts")
        vid = row.get("venue_id")
        if isinstance(ts, datetime) and ts >= cutoff and isinstance(vid, int):
            counts[vid] = counts.get(vid, 0) + 1
    return [{"venue_id": vid, "count": cnt, "window_minutes": window} for vid, cnt in counts.items()]

@app.post("/checkins")
def create_checkin(ci: CheckIn, _: str = Depends(require_login)) -> Dict[str, bool]:
    CHECKINS.append({"venue_id": ci.venue_id, "occupancy": ci.occupancy, "ts": datetime.now(timezone.utc)})
    return {"ok": True}

# -----------------------------------------------------------------------------
# Public
# -----------------------------------------------------------------------------
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}

# -----------------------------------------------------------------------------
# Simple web map (protected)
# -----------------------------------------------------------------------------
@app.get("/map", response_class=HTMLResponse)
def web_map(_: str = Depends(require_login)) -> HTMLResponse:
    html = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>SeatCheck Map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <link rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
  <style>html, body, #map { height: 100%; margin: 0; }</style>
</head>
<body>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <script>
    const YALE = [41.3083, -72.9279];
    const map = L.map('map').setView(YALE, 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

    fetch('/venues.geojson', { credentials: 'include' })
      .then(r => { if (r.status === 401) { window.location.href = '/auth/dev/login'; return {features: []}; }
                   return r.json(); })
      .then(fc => {
        (fc.features || []).forEach(f => {
          const [lon, lat] = f.geometry.coordinates;
          const name  = f.properties.name;
          const avail = f.properties.availability ?? 0.5;
          const color = avail >= 0.66 ? '#2ecc71' : (avail >= 0.33 ? '#f1c40f' : '#e74c3c');
          L.circleMarker([lat, lon], { radius: 10, color, fillColor: color, fillOpacity: 0.7, weight: 2 })
            .bindPopup(`<b>${name}</b><br/>Availability: ${(avail*100)|0}%`)
            .addTo(map);
        });
      })
      .catch(err => console.error('Failed to load venues:', err));
  </script>
</body>
</html>"""
    return HTMLResponse(html)
