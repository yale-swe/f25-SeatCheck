"""Database models for SeatCheck application."""

from datetime import datetime, timezone
from typing import Any, Optional

from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, JSON, func, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """User model for Yale students authenticated via CAS.

    Attributes:
        id: Unique identifier
        netid: Yale NetID from CAS authentication
        display_name: Optional display name chosen by user
        anonymize_checkins: Privacy setting, default True
        created_at: Account creation timestamp
        last_active_at: Last login timestamp
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # CAS authentication
    netid: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # Profile
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Privacy settings
    anonymize_checkins: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    last_active_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    checkins: Mapped[list["CheckIn"]] = relationship(
        "CheckIn", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, netid='{self.netid}')>"


class Venue(Base):
    """Venue model representing a study location.

    Attributes:
        id: Unique identifier
        name: Name of the venue (e.g., "Bass Library")
        category: Type of venue (library, cafe, lounge)
        lat: Latitude coordinate
        lon: Longitude coordinate
        description: Detailed description of the venue
        capacity: Maximum occupancy (optional)
        amenities: JSON array of amenities (e.g., ["WiFi", "Outlets"])
        accessibility: JSON array of accessibility features (e.g., ["Wheelchair"])
        opening_hours: JSON object of hours by day (e.g., {"mon": "8-22"})
        image_url: URL to venue image (optional)
        verified: Whether venue is admin-verified
        created_at: Timestamp when venue was created
        updated_at: Timestamp when venue was last updated
    """

    __tablename__ = "venues"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Required fields
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    
    # PostGIS geometry field for spatial queries
    # GEOGRAPHY type uses real-world coordinates (lat/lon) and meters for distance
    # SRID 4326 is WGS84 (standard GPS coordinate system)
    location: Mapped[Optional[Geography]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,  # Make optional during migration
    )

    # Optional fields
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    amenities: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    accessibility: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    opening_hours: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    checkins: Mapped[list["CheckIn"]] = relationship(
        "CheckIn", back_populates="venue", cascade="all, delete-orphan"
    )

    # Table configuration
    __table_args__ = (
        # Spatial index for PostGIS queries (automatically created by GeoAlchemy2)
        # This enables fast distance-based queries like ST_DWithin
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        """String representation of Venue."""
        return f"<Venue(id={self.id}, name='{self.name}')>"


# Automatic location synchronization for Venue model
@event.listens_for(Venue, "before_insert")
@event.listens_for(Venue, "before_update")
def sync_venue_location(mapper, connection, target):
    """Automatically sync PostGIS location field from lat/lon.
    
    This event listener ensures the location geometry field is always
    up-to-date when a venue is created or updated.
    """
    if target.lat is not None and target.lon is not None:
        # Create WKT (Well-Known Text) POINT geometry from lat/lon
        # Format: POINT(longitude latitude)
        target.location = WKTElement(f"POINT({target.lon} {target.lat})", srid=4326)


class CheckIn(Base):
    """CheckIn model representing a venue occupancy report.

    Attributes:
        id: Unique identifier
        venue_id: Foreign key to venues table
        user_id: Foreign key to users table
        occupancy: Occupancy level (0-5 scale, 0=empty, 5=packed)
        noise: Noise level (0-5 scale, 0=silent, 5=loud)
        anonymous: Whether check-in is anonymous (default True)
        created_at: Timestamp when check-in was created
    """

    __tablename__ = "checkins"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign keys
    venue_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("venues.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Check-in data (0-5 scale, validated at API level)
    occupancy: Mapped[int] = mapped_column(Integer, nullable=False)
    noise: Mapped[int] = mapped_column(Integer, nullable=False)

    # Privacy
    anonymous: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    venue: Mapped["Venue"] = relationship("Venue", back_populates="checkins")
    user: Mapped["User"] = relationship("User", back_populates="checkins")

    def __repr__(self) -> str:
        """String representation of CheckIn."""
        return (
            f"<CheckIn(id={self.id}, venue_id={self.venue_id}, "
            f"occupancy={self.occupancy}, noise={self.noise})>"
        )
