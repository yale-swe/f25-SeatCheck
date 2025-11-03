# backend/src/app/schemas.py
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ---- presence check-in (your existing model) ----
class CheckInIn(BaseModel):
    venue_id: int = Field(gt=0)


class CheckInOut(BaseModel):
    venue_id: int
    active: bool


# ---- ratings (David-style) ----
class RatingCreate(BaseModel):
    venue_id: int = Field(gt=0, description="Venue being rated")
    occupancy: int = Field(ge=0, le=5, description="0 empty .. 5 packed")
    noise: int = Field(ge=0, le=5, description="0 silent .. 5 very loud")
    anonymous: bool = Field(default=True)


class RatingResponse(BaseModel):
    id: int
    venue_id: int
    occupancy: int
    noise: int
    anonymous: bool
    created_at: datetime


# ---- combined venue metrics ----
class VenueWithMetrics(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    capacity: int
    # presence (your heatmap driver)
    occupancy: int
    ratio: float
    # crowd-sourced ratings (new)
    avg_occupancy: Optional[float] = None
    avg_noise: Optional[float] = None
    rating_count: int = 0


class VenueStatsResponse(BaseModel):
    venue_id: int
    # presence
    active_count: int
    window_minutes: int
    # ratings
    avg_occupancy: Optional[float] = None
    avg_noise: Optional[float] = None
    rating_count: int = 0
    last_updated: datetime
