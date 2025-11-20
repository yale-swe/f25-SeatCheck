# backend/src/app/api/v1/checkins.py
from __future__ import annotations
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_login

router = APIRouter()


class CheckInIn(BaseModel):
    venue_id: int


class CheckInOut(BaseModel):
    venue_id: int
    active: bool


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
    db.execute(
        text("""
            INSERT INTO checkins (netid, venue_id, last_seen_at)
            VALUES (:netid, :venue_id, now())
        """),
        {"netid": netid, "venue_id": payload.venue_id},
    )
    db.commit()
    return CheckInOut(venue_id=int(payload.venue_id), active=True)


@router.post("/heartbeat", response_model=CheckInOut)
def heartbeat(netid: str = Depends(require_login), db: Session = Depends(get_db)):
    row = db.execute(
        text("""
        UPDATE checkins SET last_seen_at = now()
        WHERE netid = :netid AND checkout_at IS NULL
        RETURNING venue_id
    """),
        {"netid": netid},
    ).fetchone()
    db.commit()
    return CheckInOut(venue_id=(int(row.venue_id) if row else -1), active=bool(row))


@router.post("/checkout", response_model=CheckInOut)
def checkout(netid: str = Depends(require_login), db: Session = Depends(get_db)):
    row = db.execute(
        text("""
        UPDATE checkins SET checkout_at = now()
        WHERE netid = :netid AND checkout_at IS NULL
        RETURNING venue_id
    """),
        {"netid": netid},
    ).fetchone()
    db.commit()
    return CheckInOut(venue_id=(int(row.venue_id) if row else -1), active=False)
