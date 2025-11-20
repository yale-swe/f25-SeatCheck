# backend/src/app/models.py
"""Database models for SeatCheck (aligned with Alembic core migration)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography

from app.database import Base


# -----------------------------
# Venues
# -----------------------------
class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False, index=True)
    capacity: Mapped[int] = mapped_column(
        sa.Integer, nullable=False, server_default="100"
    )

    # GEOGRAPHY(Point, 4326) – matches migration. We keep this nullable=False.
    geom: Mapped[object] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    # Provenance / external refs
    source: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default="seed")
    ext_id: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    checkins: Mapped[List["CheckIn"]] = relationship(
        "CheckIn", back_populates="venue", cascade="all, delete-orphan"
    )
    ratings: Mapped[List["Rating"]] = relationship(
        "Rating", back_populates="venue", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Venue id={self.id} name={self.name!r}>"


# -----------------------------
# Presence Check-ins (who is there now)
# -----------------------------
class CheckIn(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey("venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # We use a string identity (NetID) per the migration. If/when you add a Users table,
    # you can swap to user_id FKs and add a migration.
    netid: Mapped[str] = mapped_column(sa.Text, nullable=False, index=True)

    checkin_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
        default=lambda: datetime.now(timezone.utc),
    )
    checkout_at: Mapped[Optional[datetime]] = mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )

    # Relationship
    venue: Mapped["Venue"] = relationship("Venue", back_populates="checkins")

    def __repr__(self) -> str:
        return f"<CheckIn id={self.id} venue_id={self.venue_id} netid={self.netid!r}>"


# -----------------------------
# Anonymous Ratings (crowd + noise)
# -----------------------------
class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)
    venue_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey("venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    occupancy: Mapped[int] = mapped_column(sa.Integer, nullable=False)  # 0..5
    noise: Mapped[int] = mapped_column(sa.Integer, nullable=False)  # 0..5

    created_at: Mapped[datetime] = mapped_column(
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    venue: Mapped["Venue"] = relationship("Venue", back_populates="ratings")

    def __repr__(self) -> str:
        return f"<Rating id={self.id} venue_id={self.venue_id} occ={self.occupancy} noise={self.noise}>"
