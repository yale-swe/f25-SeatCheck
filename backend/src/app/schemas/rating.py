from datetime import datetime
from pydantic import BaseModel


class RatingCreate(BaseModel):
    venue_id: int
    occupancy: int  # 0..5
    noise: int  # 0..5
    anonymous: bool = True


class RatingResponse(BaseModel):
    id: int
    venue_id: int
    occupancy: int
    noise: int
    anonymous: bool
    created_at: datetime
