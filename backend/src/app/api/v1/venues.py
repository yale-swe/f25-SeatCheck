# backend/src/app/api/v1/venues.py
"""Venue endpoints for location data and heatmaps with image_url support."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Dict, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter()

# ---------- image URL helper (auto-matching by slug) ----------

# __file__ = .../backend/src/app/api/v1/venues.py
# parents[0]=v1, [1]=api, [2]=app, [3]=src, [4]=backend  -> backend/static
STATIC_DIR = Path(__file__).resolve().parents[4] / "static"
VENUE_IMG_DIR = STATIC_DIR / "venues"
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp")

_slug_re = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Normalize names / filenames to slugs like 'bass_library'."""
    s = text.strip().lower()
    s = _slug_re.sub("_", s).strip("_")
    return s


def build_image_map() -> Dict[str, str]:
    """
    Build a map from slug -> filename from backend/static/venues.

    Example:
      'bass_library' -> 'bass_library.jpg'
      'tsai_city' -> 'tsai_city.jpg'
    """
    mapping: Dict[str, str] = {}

    if not VENUE_IMG_DIR.exists():
        print(f"[image_url] venue image dir does not exist: {VENUE_IMG_DIR}")
        return mapping

    try:
        for p in VENUE_IMG_DIR.iterdir():
            if not p.is_file():
                continue
            if p.suffix.lower() not in IMG_EXTS:
                continue

            slug = slugify(p.stem)
            mapping[slug] = p.name
    except FileNotFoundError:
        print(f"[image_url] error iterating {VENUE_IMG_DIR}")
        return mapping

    print(f"[image_url] loaded {len(mapping)} venue images from {VENUE_IMG_DIR}")
    return mapping


# Build once at import time
IMAGE_MAP: Dict[str, str] = build_image_map()


def image_url_for_name(request: Request, name: str) -> str | None:
    """
    Map a venue name to an image URL using slug matching.

    'Bass Library' -> slug 'bass_library' -> 'bass_library.jpg' -> full URL.
    """
    slug = slugify(name)
    fname = IMAGE_MAP.get(slug)

    if not fname:
        print(f"[image_url] No image match for venue '{name}' (slug '{slug}')")
        return None

    base = str(request.base_url).rstrip("/")  # e.g., http://127.0.0.1:8000
    return f"{base}/static/venues/{fname}"


# ---------- data SQL (live occupancy + recent rating aggregates) ----------

OCC_SQL = text(
    """
WITH live AS (
  SELECT venue_id, COUNT(*) AS occupancy
  FROM checkins
  WHERE checkout_at IS NULL
    AND now() - last_seen_at <= interval '2 hours'
  GROUP BY venue_id
),
agg AS (
  SELECT venue_id,
         AVG(occupancy)::float AS avg_occupancy,
         AVG(noise)::float     AS avg_noise,
         COUNT(*)::int         AS rating_count
  FROM ratings
  WHERE created_at >= now() - interval '2 hours'
  GROUP BY venue_id
)
SELECT v.id, v.name, v.capacity,
       ST_Y(v.geom::geometry) AS lat,
       ST_X(v.geom::geometry) AS lon,
       COALESCE(live.occupancy, 0)      AS occupancy,
       COALESCE(agg.avg_occupancy, 0.0) AS avg_occupancy,
       COALESCE(agg.avg_noise, 0.0)     AS avg_noise,
       COALESCE(agg.rating_count, 0)    AS rating_count
FROM venues v
LEFT JOIN live ON live.venue_id = v.id
LEFT JOIN agg  ON agg.venue_id  = v.id
ORDER BY v.name
"""
)


@router.get("")
def list_venues(request: Request, db: Session = Depends(get_db)):
    print("[venues.list_venues] running")
    rows = db.execute(OCC_SQL).mappings().all()
    out: List[Dict[str, object]] = []
    for r in rows:
        capacity = r["capacity"]
        occ = int(r["occupancy"] or 0)
        ratio = (occ / capacity) if capacity else 0.0
        out.append(
            {
                "id": r["id"],
                "name": r["name"],
                "lat": r["lat"],
                "lon": r["lon"],
                "capacity": capacity,
                "occupancy": occ,
                "ratio": ratio,
                "avg_occupancy": r["avg_occupancy"],
                "avg_noise": r["avg_noise"],
                "rating_count": r["rating_count"],
                "image_url": image_url_for_name(request, r["name"]),
            }
        )
    return out


@router.get("/.geojson")
def venues_geojson(request: Request, db: Session = Depends(get_db)):
    rows = db.execute(OCC_SQL).mappings().all()
    features: List[Dict[str, object]] = []
    for r in rows:
        capacity = r["capacity"]
        occ = int(r["occupancy"] or 0)
        ratio = (occ / capacity) if capacity else 0.0
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                "properties": {
                    "id": r["id"],
                    "name": r["name"],
                    "capacity": capacity,
                    "occupancy": occ,
                    "ratio": ratio,
                    "avg_occupancy": r["avg_occupancy"],
                    "avg_noise": r["avg_noise"],
                    "rating_count": r["rating_count"],
                    "image_url": image_url_for_name(request, r["name"]),
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}
