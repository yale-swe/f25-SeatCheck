# backend/src/app/services/metrics.py
"""Heatmap metrics calculation service.

Computes:
- presence (active headcount) from checkins.last_seen_at
- crowd/noise aggregates from checkins_ratings.created_at
- availability as 1 - (avg_occupancy / 5), clamped to [0, 1]
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import CheckIn


def compute_venue_metrics(venue_id: int, db: Session) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    two_hours_ago = now - timedelta(hours=2)

    # --- Presence: active check-ins seen in the last 2 hours ---
    recent_count: int = (
        db.query(CheckIn)
        .filter(
            CheckIn.venue_id == venue_id,
            CheckIn.checkout_at.is_(None),
            CheckIn.last_seen_at >= two_hours_ago,
        )
        .count()
    )

    # --- Ratings: aggregate recent anonymous ratings (0..5 scales) ---
    # We use plain SQL because there's no ORM model for checkins_ratings (by design).
    stats = (
        db.execute(
            text(
                """
                SELECT
                  AVG(occupancy)::float AS avg_occupancy,
                  AVG(noise)::float     AS avg_noise,
                  COUNT(*)::int         AS rating_count,
                  MAX(created_at)       AS last_updated
                FROM checkins_ratings
                WHERE venue_id = :vid AND created_at >= :since
                """
            ),
            {"vid": venue_id, "since": two_hours_ago},
        )
        .mappings()
        .one()
    )

    avg_occ = stats["avg_occupancy"]
    avg_noise = stats["avg_noise"]
    last_updated = stats["last_updated"] or now

    # Availability: when no ratings yet, stay neutral (0.5).
    if avg_occ is None:
        availability = 0.5
    else:
        availability = max(0.0, min(1.0, 1.0 - (float(avg_occ) / 5.0)))

    return {
        "availability": availability,
        "avg_occupancy": float(avg_occ) if avg_occ is not None else None,
        "avg_noise": float(avg_noise) if avg_noise is not None else None,
        "recent_count": int(recent_count),
        "last_updated": last_updated,
    }
