# src/app/crud/checkins.py
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session


def end_active_for_user(db: Session, netid: str) -> None:
    now = datetime.now(timezone.utc)
    db.execute(
        """
        UPDATE checkins
        SET checkout_at = :now
        WHERE netid = :netid AND checkout_at IS NULL
        """,
        {"now": now, "netid": netid},
    )


def create_presence_checkin(db: Session, netid: str, venue_id: int) -> None:
    now = datetime.now(timezone.utc)
    db.execute(
        """
        INSERT INTO checkins (netid, venue_id, checkin_at, last_seen_at, checkout_at)
        VALUES (:netid, :venue_id, :now, :now, NULL)
        """,
        {"netid": netid, "venue_id": venue_id, "now": now},
    )


def heartbeat_active(db: Session, netid: str) -> int | None:
    now = datetime.now(timezone.utc)
    row = db.execute(
        """
        UPDATE checkins
        SET last_seen_at = :now
        WHERE netid = :netid AND checkout_at IS NULL
        RETURNING venue_id
        """,
        {"now": now, "netid": netid},
    ).first()
    return int(row[0]) if row else None


def occupancy_counts(db: Session, window_minutes: int = 120) -> dict[int, int]:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    rows = db.execute(
        """
        SELECT venue_id, COUNT(*)::int AS ct
        FROM checkins
        WHERE checkout_at IS NULL AND last_seen_at >= :cutoff
        GROUP BY venue_id
        """,
        {"cutoff": cutoff},
    ).fetchall()
    return {int(vid): int(ct) for vid, ct in rows}
