# src/app/schemas/rating.py
from datetime import datetime
from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    venue_id: int
    occupancy: int = Field(ge=0, le=5)
    noise: int = Field(ge=0, le=5)
    anonymous: bool = True


class RatingResponse(BaseModel):
    id: int
    venue_id: int
    occupancy: int
    noise: int
    anonymous: bool
    created_at: datetime
