# src/app/crud/presence.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Dict

from sqlalchemy import text
from sqlalchemy.orm import Session


def end_active_for_user(db: Session, netid: str) -> None:
    db.execute(
        text("""
            UPDATE checkins
            SET checkout_at = now()
            WHERE netid = :netid AND checkout_at IS NULL
        """),
        {"netid": netid},
    )
    db.commit()


def create_presence_checkin(db: Session, netid: str, venue_id: int) -> None:
    # end any existing
    end_active_for_user(db, netid)
    # create new
    db.execute(
        text("""
            INSERT INTO checkins (netid, venue_id)
            VALUES (:netid, :venue_id)
        """),
        {"netid": netid, "venue_id": venue_id},
    )
    db.commit()


def heartbeat_active(db: Session, netid: str) -> int:
    row = db.execute(
        text("""
            UPDATE checkins
            SET last_seen_at = now()
            WHERE netid = :netid AND checkout_at IS NULL
            RETURNING venue_id
        """),
        {"netid": netid},
    ).fetchone()
    db.commit()
    return int(row.venue_id) if row else -1


def occupancy_counts(db: Session, window_minutes: int = 120) -> Dict[int, int]:
    """
    Return {venue_id: active_count} for check-ins that are not checked out
    and have a last_seen_at within the window.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    rows = (
        db.execute(
            text("""
            SELECT venue_id, COUNT(*) AS cnt
            FROM checkins
            WHERE checkout_at IS NULL
              AND last_seen_at >= :cutoff
            GROUP BY venue_id
        """),
            {"cutoff": cutoff},
        )
        .mappings()
        .all()
    )
    return {int(r["venue_id"]): int(r["cnt"]) for r in rows}
