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
from pydantic import BaseModel
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
# Models & in-memory data (DB can replace this later)
# -----------------------------------------------------------------------------
class Venue(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    capacity: int = 100  # simple default until DB

VENUES: List[Venue] = [
    Venue(id=1, name="Bass Library",                lat=41.3083, lon=-72.9289, capacity=400),
    Venue(id=2, name="Sterling Memorial Library",   lat=41.3102, lon=-72.9276, capacity=600),
]

# Each check-in record:
# { netid: str, venue_id: int, checkin_at: datetime, last_seen_at: datetime, checkout_at: Optional[datetime] }
CHECKINS: List[Dict[str, object]] = []

class CheckInIn(BaseModel):
    venue_id: int

class CheckInOut(BaseModel):
    venue_id: int
    active: bool

# Helper: get active check-ins (not checked out and fresh within window)
def _active_rows(window_minutes: int = 120) -> List[Dict[str, object]]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=window_minutes)
    return [
        r for r in CHECKINS
        if r.get("checkout_at") is None and isinstance(r.get("last_seen_at"), datetime) and r["last_seen_at"] >= cutoff
    ]

def _occupancy_counts(window_minutes: int = 120) -> Dict[int, int]:
    counts = {v.id: 0 for v in VENUES}
    for r in _active_rows(window_minutes):
        vid = int(r["venue_id"])
        counts[vid] = counts.get(vid, 0) + 1
    return counts


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

@app.get("/venues/with_occupancy")
def venues_with_occupancy(window: int = 120, _: str = Depends(require_login)) -> List[Dict[str, object]]:
    counts = _occupancy_counts(window)
    out: List[Dict[str, object]] = []
    for v in VENUES:
        occ = counts.get(v.id, 0)
        ratio = (occ / v.capacity) if v.capacity else 0.0
        out.append({
            "id": v.id,
            "name": v.name,
            "lat": v.lat,
            "lon": v.lon,
            "capacity": v.capacity,
            "occupancy": occ,
            "ratio": ratio,
        })
    return out

@app.get("/venues.geojson")
def venues_geojson(_: str = Depends(require_login)) -> JSONResponse:
    counts = _occupancy_counts(120)
    features: List[Dict[str, object]] = []
    for v in VENUES:
        occ = counts.get(v.id, 0)
        ratio = (occ / v.capacity) if v.capacity else 0.0
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [v.lon, v.lat]},
            "properties": {
                "id": v.id,
                "name": v.name,
                "capacity": v.capacity,
                "occupancy": occ,
                "ratio": ratio,
            },
        })
    return JSONResponse({"type": "FeatureCollection", "features": features})

@app.get("/checkins")
def get_checkins(window: int = 120, _: str = Depends(require_login)) -> List[Dict[str, int]]:
    """Legacy/simple counts per venue for debugging."""
    counts = _occupancy_counts(window)
    return [{"venue_id": vid, "count": cnt, "window_minutes": window} for vid, cnt in counts.items()]

@app.post("/checkins", response_model=CheckInOut)
def create_checkin(ci: CheckInIn, netid: str = Depends(require_login)) -> CheckInOut:
    """End any active check-in for this user, then check in to the given venue."""
    now = datetime.now(timezone.utc)

    # End existing active (if any)
    for r in CHECKINS:
        if r["netid"] == netid and r.get("checkout_at") is None:
            r["checkout_at"] = now

    # Create new active
    CHECKINS.append({
        "netid": netid,
        "venue_id": ci.venue_id,
        "checkin_at": now,
        "last_seen_at": now,
        "checkout_at": None,
    })
    return CheckInOut(venue_id=ci.venue_id, active=True)

@app.post("/checkins/heartbeat", response_model=CheckInOut)
def heartbeat(netid: str = Depends(require_login)) -> CheckInOut:
    """Keep the current active check-in fresh."""
    now = datetime.now(timezone.utc)
    for r in CHECKINS:
        if r["netid"] == netid and r.get("checkout_at") is None:
            r["last_seen_at"] = now
            return CheckInOut(venue_id=int(r["venue_id"]), active=True)
    return CheckInOut(venue_id=-1, active=False)

@app.post("/checkins/checkout", response_model=CheckInOut)
def checkout(netid: str = Depends(require_login)) -> CheckInOut:
    """Explicitly end the current active check-in (if any)."""
    now = datetime.now(timezone.utc)
    for r in CHECKINS:
        if r["netid"] == netid and r.get("checkout_at") is None:
            r["checkout_at"] = now
            return CheckInOut(venue_id=int(r["venue_id"]), active=False)
    return CheckInOut(venue_id=-1, active=False)


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
  <style>
    html, body, #map { height:100%; margin:0; }
    .control-box { background:#fff;padding:8px 10px;border-radius:6px;box-shadow:0 1px 4px rgba(0,0,0,.2); font: 14px/1.2 system-ui,Arial; }
    .legend span { display:inline-block;width:14px;height:14px;vertical-align:middle;margin-right:6px;border-radius:3px }
    .legend .dot { margin-right:8px }
    button.btn { margin-top:6px; padding:6px 10px; border-radius:6px; border:1px solid #888; background:#fff; cursor:pointer; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <script>
    const map = L.map('map').setView([41.309, -72.927], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);

    let heatmapOn = true;
    const layerGroup = L.layerGroup().addTo(map);

    function colorFor(ratio) {
      // green -> yellow -> orange -> red
      if (ratio <= 0.25) return '#2ecc71';
      if (ratio <= 0.50) return '#bada55';
      if (ratio <= 0.75) return '#f1c40f';
      if (ratio <= 1.00) return '#e67e22';
      return '#e74c3c';
    }

    async function fetchVenues() {
      const r = await fetch('/venues/with_occupancy', { credentials: 'include' });
      if (r.status === 401) { window.location.href = '/auth/dev/login'; return []; }
      return await r.json();
    }

    function render(venues) {
      layerGroup.clearLayers();
      venues.forEach(v => {
        const ratio = v.ratio || 0;
        const color = heatmapOn ? colorFor(ratio) : '#3388ff';
        const radius = heatmapOn ? Math.max(8, 30 * Math.min(1, ratio + 0.15)) : 8;

        const marker = L.circleMarker([v.lat, v.lon], {
          radius, color, fillColor: color, fillOpacity: 0.75, weight: heatmapOn ? 0 : 2
        }).bindPopup(`
          <b>${v.name}</b><br/>
          ${v.occupancy}/${v.capacity} occupied (${Math.round(ratio*100)}%)<br/>
          <button class="btn" id="btn-${v.id}">Check in here</button>
        `);

        marker.on('popupopen', () => {
          const btn = document.getElementById(`btn-${v.id}`);
          if (btn) btn.onclick = async () => {
            const res = await fetch('/checkins', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              credentials: 'include',
              body: JSON.stringify({ venue_id: v.id })
            });
            if (res.ok) { fetchAndRender(); }
            else { alert('Check-in failed or login required.'); }
          };
        });

        layerGroup.addLayer(marker);
      });
    }

    async function fetchAndRender() {
      const venues = await fetchVenues();
      render(venues);
    }

    // Toggle control
    const ctrl = L.control({ position: 'topright' });
    ctrl.onAdd = function() {
      const div = L.DomUtil.create('div', 'control-box');
      div.innerHTML = `
        <label><input id="heatToggle" type="checkbox" checked /> Heatmap</label>
        <div class="legend" style="margin-top:6px">
          <span class="dot" style="background:#2ecc71"></span>Empty
          <span class="dot" style="background:#f1c40f"></span>Busy
          <span class="dot" style="background:#e74c3c"></span>Full
        </div>
        <button class="btn" id="checkoutBtn">Check out</button>
      `;
      return div;
    };
    ctrl.addTo(map);

    document.addEventListener('change', (e) => {
      if (e.target && e.target.id === 'heatToggle') {
        heatmapOn = e.target.checked;
        fetchAndRender();
      }
    });

    document.addEventListener('click', async (e) => {
      if (e.target && e.target.id === 'checkoutBtn') {
        await fetch('/checkins/checkout', { method: 'POST', credentials: 'include' });
        fetchAndRender();
      }
    });

    // Polling + heartbeat
    fetchAndRender();
    setInterval(fetchAndRender, 15000); // refresh every 15s
    setInterval(() => fetch('/checkins/heartbeat', { method: 'POST', credentials: 'include' }), 60000);
  </script>
</body>
</html>"""
    return HTMLResponse(html)
