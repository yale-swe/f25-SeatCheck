"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Check-In Schemas
# ============================================================================


class CheckInCreate(BaseModel):
    """Schema for creating a new check-in.
    
    Used by POST /api/v1/checkins endpoint.
    """

    venue_id: int = Field(..., description="ID of the venue being checked into", gt=0)
    occupancy: int = Field(
        ...,
        description="Occupancy level (0=empty, 5=packed)",
        ge=0,
        le=5,
    )
    noise: int = Field(
        ...,
        description="Noise level (0=silent, 5=very loud)",
        ge=0,
        le=5,
    )
    anonymous: bool = Field(
        default=True,
        description="Whether check-in should be anonymous",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "venue_id": 1,
                "occupancy": 3,
                "noise": 2,
                "anonymous": True,
            }
        }
    )


class CheckInResponse(BaseModel):
    """Schema for check-in response.
    
    Returned by POST /api/v1/checkins endpoint.
    """

    id: int = Field(..., description="Unique check-in ID")
    venue_id: int = Field(..., description="Venue ID")
    user_id: int = Field(..., description="User ID who made the check-in")
    occupancy: int = Field(..., description="Occupancy level (0-5)")
    noise: int = Field(..., description="Noise level (0-5)")
    anonymous: bool = Field(..., description="Whether check-in is anonymous")
    created_at: datetime = Field(..., description="When check-in was created")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 123,
                "venue_id": 1,
                "user_id": 1,
                "occupancy": 3,
                "noise": 2,
                "anonymous": True,
                "created_at": "2025-10-28T12:34:56Z",
            }
        },
    )


# ============================================================================
# Venue Statistics Schemas
# ============================================================================


class VenueStatsResponse(BaseModel):
    """Schema for venue statistics response.
    
    Returns aggregated check-in data for a venue.
    Used by GET /api/v1/venues/{venue_id}/stats endpoint.
    """

    venue_id: int = Field(..., description="Venue ID")
    avg_occupancy: Optional[float] = Field(
        None,
        description="Average occupancy from recent check-ins (0-5 scale)",
        ge=0,
        le=5,
    )
    avg_noise: Optional[float] = Field(
        None,
        description="Average noise level from recent check-ins (0-5 scale)",
        ge=0,
        le=5,
    )
    checkin_count: int = Field(
        ...,
        description="Number of check-ins in time window",
        ge=0,
    )
    time_window_minutes: int = Field(
        default=2,
        description="Time window for aggregation in minutes",
    )
    last_updated: datetime = Field(
        ...,
        description="When these stats were calculated",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "venue_id": 1,
                "avg_occupancy": 3.2,
                "avg_noise": 2.1,
                "checkin_count": 5,
                "time_window_minutes": 2,
                "last_updated": "2025-10-28T12:34:56Z",
            }
        }
    )


# ============================================================================
# Venue Schemas (Basic - for listing)
# ============================================================================


class VenueResponse(BaseModel):
    """Schema for venue response."""

    id: int
    name: str
    category: str
    lat: float
    lon: float
    description: Optional[str] = None
    capacity: Optional[int] = None
    verified: bool

    model_config = ConfigDict(from_attributes=True)

