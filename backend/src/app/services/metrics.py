"""Heatmap metrics calculation service.

Provides time-decayed aggregation for venue occupancy and noise levels.
"""

from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import CheckIn


def compute_venue_metrics(venue_id: int, db: Session) -> dict[str, Any]:
    """Compute time-decayed availability, occupancy, and noise metrics for a venue.

    Uses exponential decay with 30-minute half-life to weigh recent check-ins
    more heavily than older ones.

    Args:
        venue_id: ID of the venue to compute metrics for
        db: Database session

    Returns:
        Dictionary containing:
            - availability: Score from 0 (full) to 1 (empty)
            - avg_occupancy: Weighted average occupancy (0-5 scale)
            - avg_noise: Weighted average noise level (0-5 scale)
            - recent_count: Number of check-ins in the last hour
            - last_updated: Timestamp of most recent check-in
    """
    now = datetime.now(timezone.utc)
    half_life = timedelta(minutes=30)
    tau = half_life / 0.69314718056  # ln(2)

    # Get recent check-ins (last 2 hours to include enough data for decay)
    two_hours_ago = now - timedelta(hours=2)
    checkins = (
        db.query(CheckIn)
        .filter(CheckIn.venue_id == venue_id, CheckIn.created_at >= two_hours_ago)
        .all()
    )

    if not checkins:
        return {
            "availability": 0.5,  # Neutral default when no data
            "avg_occupancy": 0.0,
            "avg_noise": 0.0,
            "recent_count": 0,
            "last_updated": None,
        }

    # Compute time-decayed weighted averages
    weighted_availability = 0.0
    weighted_occupancy = 0.0
    weighted_noise = 0.0
    total_weight = 0.0

    for checkin in checkins:
        dt = (now - checkin.created_at).total_seconds()
        weight = pow(2.718281828, -(dt / tau.total_seconds()))

        # Availability = 1 - normalized occupancy
        availability = 1.0 - (checkin.occupancy / 5.0)

        weighted_availability += availability * weight
        weighted_occupancy += checkin.occupancy * weight
        weighted_noise += checkin.noise * weight
        total_weight += weight

    # Get count of very recent check-ins (last hour)
    one_hour_ago = now - timedelta(hours=1)
    recent_count = (
        db.query(func.count(CheckIn.id))
        .filter(CheckIn.venue_id == venue_id, CheckIn.created_at >= one_hour_ago)
        .scalar()
    )

    return {
        "availability": max(0.0, min(1.0, weighted_availability / total_weight)),
        "avg_occupancy": weighted_occupancy / total_weight,
        "avg_noise": weighted_noise / total_weight,
        "recent_count": recent_count or 0,
        "last_updated": max(c.created_at for c in checkins),
    }
