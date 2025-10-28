"""CRUD operations for check-ins."""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import CheckIn, Venue
from app.schemas import CheckInCreate


def create_checkin(
    db: Session,
    checkin_data: CheckInCreate,
    user_id: int,
) -> CheckIn:
    """Create a new check-in record.
    
    Args:
        db: Database session
        checkin_data: Check-in data from request
        user_id: ID of user making the check-in (from auth)
    
    Returns:
        Created CheckIn object
    
    Raises:
        ValueError: If venue_id doesn't exist
    """
    # Verify venue exists
    venue = db.query(Venue).filter(Venue.id == checkin_data.venue_id).first()
    if not venue:
        raise ValueError(f"Venue with id {checkin_data.venue_id} not found")
    
    # Create check-in
    db_checkin = CheckIn(
        venue_id=checkin_data.venue_id,
        user_id=user_id,
        occupancy=checkin_data.occupancy,
        noise=checkin_data.noise,
        anonymous=checkin_data.anonymous,
        created_at=datetime.now(timezone.utc),
    )
    
    db.add(db_checkin)
    db.commit()
    db.refresh(db_checkin)
    
    return db_checkin


def get_recent_checkins(
    db: Session,
    venue_id: int,
    minutes: int = 2,
) -> list[CheckIn]:
    """Get recent check-ins for a venue.
    
    Args:
        db: Database session
        venue_id: Venue ID to get check-ins for
        minutes: How many minutes back to look (default: 2)
    
    Returns:
        List of CheckIn objects from the last N minutes
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    return (
        db.query(CheckIn)
        .filter(
            CheckIn.venue_id == venue_id,
            CheckIn.created_at >= cutoff_time,
        )
        .order_by(CheckIn.created_at.desc())
        .all()
    )


def get_venue_stats(
    db: Session,
    venue_id: int,
    minutes: int = 2,
) -> dict[str, Optional[float | int]]:
    """Get aggregated statistics for a venue.
    
    Calculates average occupancy and noise from recent check-ins.
    
    Args:
        db: Database session
        venue_id: Venue ID to get stats for
        minutes: Time window in minutes (default: 2)
    
    Returns:
        Dictionary with keys:
        - avg_occupancy: Average occupancy (0-5) or None if no check-ins
        - avg_noise: Average noise (0-5) or None if no check-ins
        - checkin_count: Number of check-ins in window
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    # Query for aggregated stats
    result = (
        db.query(
            func.avg(CheckIn.occupancy).label("avg_occupancy"),
            func.avg(CheckIn.noise).label("avg_noise"),
            func.count(CheckIn.id).label("checkin_count"),
        )
        .filter(
            CheckIn.venue_id == venue_id,
            CheckIn.created_at >= cutoff_time,
        )
        .first()
    )
    
    # Handle case where no check-ins exist
    if result.checkin_count == 0:
        return {
            "avg_occupancy": None,
            "avg_noise": None,
            "checkin_count": 0,
        }
    
    return {
        "avg_occupancy": float(result.avg_occupancy) if result.avg_occupancy is not None else None,
        "avg_noise": float(result.avg_noise) if result.avg_noise is not None else None,
        "checkin_count": int(result.checkin_count),
    }


def get_all_venues_stats(
    db: Session,
    minutes: int = 2,
) -> dict[int, dict[str, Optional[float | int]]]:
    """Get aggregated statistics for all venues.
    
    Useful for displaying availability across all venues at once.
    
    Args:
        db: Database session
        minutes: Time window in minutes (default: 2)
    
    Returns:
        Dictionary mapping venue_id to stats dict
    """
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    
    # Query for aggregated stats grouped by venue
    results = (
        db.query(
            CheckIn.venue_id,
            func.avg(CheckIn.occupancy).label("avg_occupancy"),
            func.avg(CheckIn.noise).label("avg_noise"),
            func.count(CheckIn.id).label("checkin_count"),
        )
        .filter(CheckIn.created_at >= cutoff_time)
        .group_by(CheckIn.venue_id)
        .all()
    )
    
    # Convert to dictionary
    stats_by_venue = {}
    for row in results:
        stats_by_venue[row.venue_id] = {
            "avg_occupancy": float(row.avg_occupancy) if row.avg_occupancy is not None else None,
            "avg_noise": float(row.avg_noise) if row.avg_noise is not None else None,
            "checkin_count": int(row.checkin_count),
        }
    
    return stats_by_venue

