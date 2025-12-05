# backend/src/app/api/v1/ratings.py
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_login
from app.models import Venue, Rating

router = APIRouter()

Int05 = Annotated[int, Field(ge=0, le=5)]


class RatingCreatePayload(BaseModel):
    venue_id: int
    occupancy: Int05 | None = None  # 0–5 or null
    noise: Int05 | None = None  # 0–5 or null


class RatingOut(BaseModel):
    id: int
    venue_id: int
    occupancy: int | None
    noise: int | None
    created_at: datetime


@router.post("", status_code=status.HTTP_201_CREATED, response_model=RatingOut)
def create_rating(
    payload: RatingCreatePayload,
    netid: str = Depends(require_login),
    db: Session = Depends(get_db),
):
    venue = db.get(Venue, payload.venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    rating = Rating(
        venue_id=payload.venue_id,
        occupancy=payload.occupancy if payload.occupancy is not None else 0,
        noise=payload.noise if payload.noise is not None else 0,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return RatingOut(
        id=rating.id,
        venue_id=rating.venue_id,
        occupancy=rating.occupancy,
        noise=rating.noise,
        created_at=rating.created_at,
    )
