# backend/src/app/schemas/checkin.py
"""Check-in related schemas (Pydantic models)."""

from typing import Optional
from pydantic import BaseModel, Field


# --- Presence check-in (used by main.py) ---
class CheckInIn(BaseModel):
    """Presence check-in request: start a check-in at a venue."""

    venue_id: int


class CheckInOut(BaseModel):
    """Presence check-in response used by create/heartbeat/checkout."""

    venue_id: int
    active: bool


# --- Rating-style check-in (used by api/v1/checkins.py) ---
class CheckInRequest(BaseModel):
    """Request schema for recording a rating-like check-in event."""

    venue_id: int
    occupancy: int = Field(ge=0, le=5, description="0=empty, 5=packed")
    noise: int = Field(ge=0, le=5, description="0=silent, 5=loud")
    user_id: Optional[int] = Field(
        default=None,
        description="Optional for MVP; may be required with auth later.",
    )


class CheckInResponse(BaseModel):
    """Response schema for rating-like check-in."""

    ok: bool
    checkin_id: int
    message: str = "Check-in recorded successfully"
