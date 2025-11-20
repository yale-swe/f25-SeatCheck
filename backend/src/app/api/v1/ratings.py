# backend/src/app/api/v1/ratings.py
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Venue, Rating

router = APIRouter()

Int05 = Annotated[int, Field(ge=0, le=5)]


class RatingCreatePayload(BaseModel):
    venue_id: int
    occupancy: Int05  # 0–5
    noise: Int05  # 0–5


@router.post("", status_code=status.HTTP_201_CREATED)
def create_rating(payload: RatingCreatePayload, db: Session = Depends(get_db)):
    venue = db.get(Venue, payload.venue_id)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    rating = Rating(
        venue_id=payload.venue_id,
        occupancy=payload.occupancy,
        noise=payload.noise,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return {"id": rating.id}
