# backend/src/app/main.py
from __future__ import annotations

import os
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import text
from .db import SessionLocal

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(filename=".env"))

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------
app = FastAPI(title="SeatCheck API", version="0.1.0")

# ---- Frontend base ----------------------------------------------------------
APP_BASE = os.getenv("APP_BASE", "http://localhost:8081")

# ---- CORS -------------------------------------------------------------------
default_origins = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
]
extra_origins = os.getenv("DEV_ORIGINS", "").split(",") if os.getenv("DEV_ORIGINS") else []
DEV_ORIGINS = list(set(default_origins + extra_origins))

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
# DB dependency (keep)
# -----------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------------------------
# I/O models (keep minimal Pydantic models for request/response)
# -----------------------------------------------------------------------------
class CheckInIn(BaseModel):
    venue_id: int

class CheckInOut(BaseModel):
    venue_id: int
    active: bool

# -----------------------------------------------------------------------------
# SQL helpers (NEW) — replaces in-memory helpers
# -----------------------------------------------------------------------------
VENUES_SQL = text("""
SELECT id, name, capacity,
       ST_X(ST_Transform(geom::geometry, 4326)) AS lon,
       ST_Y(ST_Transform(geom::geometry, 4326)) AS lat
FROM venues
ORDER BY name
""")

OCC_SQL = text("""
SELECT v.id, v.name, v.capacity,
       ST_X(ST_Transform(v.geom::geometry, 4326)) AS lon,
       ST_Y(ST_Transform(v.geom::geometry, 4326)) AS lat,
       COALESCE(o.occupancy, 0) AS occupancy
FROM venues v
LEFT JOIN (
  SELECT venue_id, COUNT(*) AS occupancy
  FROM checkins
  WHERE checkout_at IS NULL
    AND now() - last_seen_at <= interval '2 hours'
  GROUP BY venue_id
) o ON o.venue_id = v.id
ORDER BY v.name
""")

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
# Protected app API (DB-backed now)
# -----------------------------------------------------------------------------
@app.get("/venues")
def list_venues(_: str = Depends(require_login), db: Session = Depends(get_db)):
    rows = db.execute(VENUES_SQL).mappings().all()
    return [
        {"id": r["id"], "name": r["name"], "capacity": r["capacity"], "lat": r["lat"], "lon": r["lon"]}
        for r in rows
    ]

@app.get("/venues/with_occupancy")
def venues_with_occupancy(_: str = Depends(require_login), db: Session = Depends(get_db)):
    rows = db.execute(OCC_SQL).mappings().all()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "lat": r["lat"],
            "lon": r["lon"],
            "capacity": r["capacity"],
            "occupancy": r["occupancy"],
            "ratio": (r["occupancy"] / r["capacity"]) if r["capacity"] else 0.0,
        }
        for r in rows
    ]

@app.get("/venues.geojson")
def venues_geojson(_: str = Depends(require_login), db: Session = Depends(get_db)) -> JSONResponse:
    rows = db.execute(OCC_SQL).mappings().all()
    features: List[Dict[str, object]] = []
    for r in rows:
        ratio = (r["occupancy"] / r["capacity"]) if r["capacity"] else 0.0
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                "id": r["id"],
                "name": r["name"],
                "capacity": r["capacity"],
                "occupancy": r["occupancy"],
                "ratio": ratio,
            },
        })
    return JSONResponse({"type": "FeatureCollection", "features": features})

@app.get("/checkins")
def get_checkins(window: int = 120, _: str = Depends(require_login), db: Session = Depends(get_db)):
    rows = db.execute(text(f"""
        SELECT v.id AS venue_id,
               COALESCE(o.count, 0) AS count
        FROM venues v
        LEFT JOIN (
          SELECT venue_id, COUNT(*) AS count
          FROM checkins
          WHERE checkout_at IS NULL
            AND now() - last_seen_at <= interval '{window} minutes'
          GROUP BY venue_id
        ) o ON o.venue_id = v.id
        ORDER BY v.id
    """)).mappings().all()
    return [{"venue_id": r["venue_id"], "count": r["count"], "window_minutes": window} for r in rows]

@app.post("/checkins", response_model=CheckInOut)
def create_checkin(ci: CheckInIn, netid: str = Depends(require_login), db: Session = Depends(get_db)) -> CheckInOut:
    # end any existing active check-in for this user, then create new
    db.execute(text("""
        UPDATE checkins SET checkout_at = now()
        WHERE netid = :netid AND checkout_at IS NULL
    """), {"netid": netid})
    db.execute(text("""
        INSERT INTO checkins (netid, venue_id) VALUES (:netid, :venue_id)
    """), {"netid": netid, "venue_id": ci.venue_id})
    db.commit()
    return CheckInOut(venue_id=ci.venue_id, active=True)

@app.post("/checkins/heartbeat", response_model=CheckInOut)
def heartbeat(netid: str = Depends(require_login), db: Session = Depends(get_db)) -> CheckInOut:
    row = db.execute(text("""
        UPDATE checkins SET last_seen_at = now()
        WHERE netid = :netid AND checkout_at IS NULL
        RETURNING venue_id
    """), {"netid": netid}).fetchone()
    db.commit()
    return CheckInOut(venue_id=(row.venue_id if row else -1), active=bool(row))

@app.post("/checkins/checkout", response_model=CheckInOut)
def checkout(netid: str = Depends(require_login), db: Session = Depends(get_db)) -> CheckInOut:
    row = db.execute(text("""
        UPDATE checkins SET checkout_at = now()
        WHERE netid = :netid AND checkout_at IS NULL
        RETURNING venue_id
    """), {"netid": netid}).fetchone()
    db.commit()
    return CheckInOut(venue_id=(row.venue_id if row else -1), active=False)

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
