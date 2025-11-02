# backend/src/app/crud/ratings.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy import func, text
from sqlalchemy.orm import Session

def create_rating(
    db: Session,
    *,
    venue_id: int,
    netid: Optional[str],
    occupancy: int,
    noise: int,
    anonymous: bool,
):
    row = db.execute(
        """
        INSERT INTO checkins_ratings (venue_id, netid, occupancy, noise, anonymous, created_at)
        VALUES (:venue_id, :netid, :occupancy, :noise, :anonymous, :created_at)
        RETURNING id, venue_id, occupancy, noise, anonymous, created_at
        """,
        {
            "venue_id": venue_id,
            "netid": (None if anonymous else netid),
            "occupancy": occupancy,
            "noise": noise,
            "anonymous": anonymous,
            "created_at": datetime.now(timezone.utc),
        },
    ).first()
    db.commit()
    return row  # Row object with fields as selected


def get_venue_rating_stats(
    db: Session,
    venue_id: int,
    minutes: int = 120,
) -> dict[str, Optional[float | int]]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    row = db.execute(
        text("""
            SELECT
              AVG(occupancy)::float  AS avg_occupancy,
              AVG(noise)::float      AS avg_noise,
              COUNT(*)::int          AS rating_count
            FROM checkins_ratings
            WHERE venue_id = :venue_id
              AND created_at >= :cutoff
        """),
        {"venue_id": venue_id, "cutoff": cutoff},
    ).mappings().first()

    if not row:
        return {"avg_occupancy": None, "avg_noise": None, "rating_count": 0}

    return {
        "avg_occupancy": row["avg_occupancy"],
        "avg_noise": row["avg_noise"],
        "rating_count": row["rating_count"],
    }

def get_all_rating_stats(
    db: Session,
    minutes: int = 120,
) -> dict[int, dict[str, Optional[float | int]]]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    rows = db.execute(
        text("""
            SELECT
              venue_id,
              AVG(occupancy)::float  AS avg_occupancy,
              AVG(noise)::float      AS avg_noise,
              COUNT(*)::int          AS rating_count
            FROM checkins_ratings
            WHERE created_at >= :cutoff
            GROUP BY venue_id
        """),
        {"cutoff": cutoff},
    ).mappings().all()

    stats: dict[int, dict[str, Optional[float | int]]]= {}
    for r in rows:
        stats[int(r["venue_id"])] = {
            "avg_occupancy": r["avg_occupancy"],
            "avg_noise": r["avg_noise"],
            "rating_count": r["rating_count"],
        }
    return stats
