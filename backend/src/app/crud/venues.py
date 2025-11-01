"""CRUD operations for venues with PostGIS spatial queries."""

from typing import Optional

from geoalchemy2 import functions as geo_func
from sqlalchemy import cast, Float
from sqlalchemy.orm import Session

from app.models import Venue


def get_venue_by_id(db: Session, venue_id: int) -> Optional[Venue]:
    """Get a venue by ID.
    
    Args:
        db: Database session
        venue_id: Venue ID to retrieve
    
    Returns:
        Venue object if found, None otherwise
    """
    return db.query(Venue).filter(Venue.id == venue_id).first()


def get_all_venues(db: Session, skip: int = 0, limit: int = 100) -> list[Venue]:
    """Get all venues with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of Venue objects
    """
    return db.query(Venue).offset(skip).limit(limit).all()


def get_nearby_venues(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float = 1000.0,
    limit: int = 20,
) -> list[tuple[Venue, float]]:
    """Find venues within a radius of a given location.
    
    Uses PostGIS ST_DWithin for efficient spatial query with distance calculation.
    
    Args:
        db: Database session
        latitude: Latitude of center point
        longitude: Longitude of center point
        radius_meters: Search radius in meters (default: 1000m = 1km)
        limit: Maximum number of results
    
    Returns:
        List of tuples (Venue, distance_meters) sorted by distance
    
    Example:
        >>> venues = get_nearby_venues(db, 41.3083, -72.9289, 500)
        >>> for venue, distance in venues:
        ...     print(f"{venue.name}: {distance:.0f}m away")
    """
    # Create a point from the input lat/lon
    point = f"SRID=4326;POINT({longitude} {latitude})"
    
    # Query for venues within radius, ordered by distance
    # ST_DWithin is very efficient because it uses the spatial index
    # ST_Distance calculates the actual distance for display
    results = (
        db.query(
            Venue,
            cast(
                geo_func.ST_Distance(
                    Venue.location,
                    geo_func.ST_GeogFromText(point)
                ),
                Float
            ).label("distance")
        )
        .filter(
            geo_func.ST_DWithin(
                Venue.location,
                geo_func.ST_GeogFromText(point),
                radius_meters
            )
        )
        .order_by("distance")
        .limit(limit)
        .all()
    )
    
    return [(venue, distance) for venue, distance in results]


def get_nearest_venue(
    db: Session,
    latitude: float,
    longitude: float,
) -> Optional[tuple[Venue, float]]:
    """Find the nearest venue to a given location.
    
    Args:
        db: Database session
        latitude: Latitude of reference point
        longitude: Longitude of reference point
    
    Returns:
        Tuple of (Venue, distance_meters) or None if no venues exist
    
    Example:
        >>> venue, distance = get_nearest_venue(db, 41.3083, -72.9289)
        >>> print(f"Nearest venue: {venue.name} ({distance:.0f}m away)")
    """
    point = f"SRID=4326;POINT({longitude} {latitude})"
    
    result = (
        db.query(
            Venue,
            cast(
                geo_func.ST_Distance(
                    Venue.location,
                    geo_func.ST_GeogFromText(point)
                ),
                Float
            ).label("distance")
        )
        .order_by("distance")
        .first()
    )
    
    if result:
        venue, distance = result
        return (venue, distance)
    return None


def get_venues_in_bounding_box(
    db: Session,
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
) -> list[Venue]:
    """Get all venues within a bounding box (useful for map viewport queries).
    
    Args:
        db: Database session
        min_lat: Minimum latitude (south)
        max_lat: Maximum latitude (north)
        min_lon: Minimum longitude (west)
        max_lon: Maximum longitude (east)
    
    Returns:
        List of venues within the bounding box
    
    Example:
        >>> # Get venues visible in current map viewport
        >>> venues = get_venues_in_bounding_box(
        ...     db, 41.30, 41.32, -72.94, -72.92
        ... )
    """
    # For GEOGRAPHY types, use simple lat/lon comparison instead of ST_Within
    # This is actually more efficient for bounding box queries
    return (
        db.query(Venue)
        .filter(
            Venue.lat >= min_lat,
            Venue.lat <= max_lat,
            Venue.lon >= min_lon,
            Venue.lon <= max_lon
        )
        .all()
    )


def calculate_distance_between_venues(
    db: Session,
    venue_id_1: int,
    venue_id_2: int,
) -> Optional[float]:
    """Calculate distance between two venues in meters.
    
    Args:
        db: Database session
        venue_id_1: First venue ID
        venue_id_2: Second venue ID
    
    Returns:
        Distance in meters, or None if either venue doesn't exist
    
    Example:
        >>> distance = calculate_distance_between_venues(db, 1, 2)
        >>> print(f"Distance: {distance:.0f} meters")
    """
    venue1 = db.query(Venue).filter(Venue.id == venue_id_1).first()
    venue2 = db.query(Venue).filter(Venue.id == venue_id_2).first()
    
    if not venue1 or not venue2:
        return None
    
    result = db.query(
        cast(
            geo_func.ST_Distance(venue1.location, venue2.location),
            Float
        )
    ).scalar()
    
    return result

