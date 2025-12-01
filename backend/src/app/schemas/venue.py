"""Venue-related schemas (Pydantic models)."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Venue(BaseModel):
    id: int
    name: str
    capacity: int
    lat: float
    lon: float
    image_url: Optional[str] = None


class VenueWithMetrics(Venue):
    occupancy: int
    ratio: float
    avg_occupancy: Optional[float] = None
    avg_noise: Optional[float] = None
    rating_count: int = 0


class VenueStatsResponse(BaseModel):
    venue_id: int
    active_count: int
    window_minutes: int
    avg_occupancy: Optional[float] = None
    avg_noise: Optional[float] = None
    rating_count: int = 0
    last_updated: datetime


class VenueStatus(BaseModel):
    venue_id: int
    venue_name: str
    availability: float  # 0=full, 1=empty
    avg_occupancy: float
    avg_noise: float
    recent_checkins_count: int
    last_updated: Optional[datetime] = None
