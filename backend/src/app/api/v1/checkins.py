# backend/src/app/api/v1/checkins.py
from __future__ import annotations
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.api.deps import get_db, require_login

router = APIRouter()


class CheckInIn(BaseModel):
    venue_id: int


class CheckInOut(BaseModel):
    venue_id: int
    active: bool
    checkin_at: datetime
    last_seen_at: datetime
    checkout_at: datetime | None


class CheckInCountItem(BaseModel):
    venue_id: int
    count: int


@router.post("", response_model=CheckInOut)
def create_checkin(
    payload: CheckInIn,
    netid: str = Depends(require_login),
    db: Session = Depends(get_db),
):
    # end any existing active checkin
    db.execute(
        text(
            "UPDATE checkins SET checkout_at = now() WHERE netid = :netid AND checkout_at IS NULL"
        ),
        {"netid": netid},
    )
    # insert and mark last_seen_at now so it counts immediately
    try:
        db.execute(
            text("""
                INSERT INTO checkins (netid, venue_id, last_seen_at)
                VALUES (:netid, :venue_id, now())
            """),
            {"netid": netid, "venue_id": payload.venue_id},
        )
        db.commit()
    except IntegrityError as e:
        # Likely a foreign key violation (invalid venue_id)
        db.rollback()
        raise HTTPException(status_code=422, detail="Invalid venue_id") from e
    # fetch back the created record
    row = db.execute(
        text("""
            SELECT checkin_at, last_seen_at, checkout_at
            FROM checkins
            WHERE netid = :netid AND checkout_at IS NULL
            ORDER BY checkin_at DESC
            LIMIT 1
        """),
        {"netid": netid},
    ).fetchone()
    return CheckInOut(
        venue_id=int(payload.venue_id),
        active=True,
        checkin_at=row.checkin_at,
        last_seen_at=row.last_seen_at,
        checkout_at=row.checkout_at,
    )


@router.post("/heartbeat", response_model=CheckInOut)
def heartbeat(netid: str = Depends(require_login), db: Session = Depends(get_db)):
    row = db.execute(
        text("""
        UPDATE checkins SET last_seen_at = now()
        WHERE netid = :netid AND checkout_at IS NULL
        RETURNING venue_id, checkin_at, last_seen_at, checkout_at
    """),
        {"netid": netid},
    ).fetchone()
    db.commit()
    if row:
        return CheckInOut(
            venue_id=int(row.venue_id),
            active=True,
            checkin_at=row.checkin_at,
            last_seen_at=row.last_seen_at,
            checkout_at=row.checkout_at,
        )
    else:
        # No active checkin; return defaults
        return CheckInOut(
            venue_id=-1,
            active=False,
            checkin_at=datetime.now(),
            last_seen_at=datetime.now(),
            checkout_at=None,
        )


@router.post("/checkout", response_model=CheckInOut)
def checkout(netid: str = Depends(require_login), db: Session = Depends(get_db)):
    row = db.execute(
        text("""
        UPDATE checkins SET checkout_at = now()
        WHERE netid = :netid AND checkout_at IS NULL
        RETURNING venue_id, checkin_at, last_seen_at, checkout_at
    """),
        {"netid": netid},
    ).fetchone()
    db.commit()
    if row:
        return CheckInOut(
            venue_id=int(row.venue_id),
            active=False,
            checkin_at=row.checkin_at,
            last_seen_at=row.last_seen_at,
            checkout_at=row.checkout_at,
        )
    else:
        # No active checkin to checkout
        return CheckInOut(
            venue_id=-1,
            active=False,
            checkin_at=datetime.now(),
            last_seen_at=datetime.now(),
            checkout_at=None,
        )


@router.get("", response_model=List[CheckInCountItem])
def get_checkin_counts(
    netid: str = Depends(require_login),
    db: Session = Depends(get_db),
    window: int = 120,
):
    """Get count of active check-ins per venue within time window (minutes)."""
    rows = db.execute(
        text("""
            SELECT venue_id, COUNT(*) as count
            FROM checkins
            WHERE checkout_at IS NULL
              AND now() - last_seen_at <= interval ':window minutes'
            GROUP BY venue_id
            ORDER BY venue_id
        """),
        {"window": window},
    ).all()
    return [
        CheckInCountItem(venue_id=int(r.venue_id), count=int(r.count)) for r in rows
    ]
