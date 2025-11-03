"""Venue related schemas (Pydantic models)."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class VenueStatus(BaseModel):
    """Detailed status information for a venue including heatmap metrics."""

    venue_id: int
    venue_name: str
    availability: float = Field(
        ge=0.0, le=1.0, description="Availability score: 0=full, 1=empty"
    )
    avg_occupancy: float = Field(ge=0.0, le=5.0, description="Average occupancy level")
    avg_noise: float = Field(ge=0.0, le=5.0, description="Average noise level")
    recent_checkins_count: int = Field(description="Number of check-ins in last hour")
    last_updated: Optional[datetime] = Field(
        description="Timestamp of most recent check-in"
    )
