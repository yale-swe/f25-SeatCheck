"""Check-in related schemas (Pydantic models)."""

from typing import Optional
from pydantic import BaseModel, Field


class CheckInRequest(BaseModel):
    """Request schema for creating a check-in."""

    venue_id: int
    occupancy: int = Field(ge=0, le=5, description="Occupancy level: 0=empty, 5=packed")
    noise: int = Field(ge=0, le=5, description="Noise level: 0=silent, 5=loud")
    user_id: Optional[int] = Field(
        default=None,
        description="User ID (optional for MVP, will be required with auth)",
    )


class CheckInResponse(BaseModel):
    """Response schema for check-in creation."""

    ok: bool
    checkin_id: int
    message: str = "Check-in recorded successfully"
