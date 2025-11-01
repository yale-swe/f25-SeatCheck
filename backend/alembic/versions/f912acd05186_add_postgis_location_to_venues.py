"""add_postgis_location_to_venues

Revision ID: f912acd05186
Revises: 50a654c32b1f
Create Date: 2025-11-01 14:31:14.778628

This migration adds PostGIS support for location tracking:
1. Enables PostGIS extension
2. Adds location geometry column to venues table
3. Populates location from existing lat/lon data
4. Creates spatial index for fast distance queries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'f912acd05186'
down_revision: Union[str, Sequence[str], None] = '50a654c32b1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to add PostGIS location tracking."""
    # Step 1: Enable PostGIS extension
    # Note: Extension should be enabled manually first: psql -d seatcheck -c "CREATE EXTENSION postgis;"
    # Commenting out to avoid permission issues - enable manually if needed
    # op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    
    # Step 2: Add location column as GEOGRAPHY(POINT, 4326)
    # GEOGRAPHY type uses real-world coordinates and meters for distance
    # SRID 4326 is WGS84 (standard GPS coordinate system)
    op.execute("""
        ALTER TABLE venues 
        ADD COLUMN location GEOGRAPHY(POINT, 4326)
    """)
    
    # Step 3: Populate location from existing lat/lon data
    # ST_SetSRID creates a point with the specified coordinate system
    op.execute("""
        UPDATE venues 
        SET location = ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
        WHERE lat IS NOT NULL AND lon IS NOT NULL
    """)
    
    # Step 4: Create spatial index for fast distance queries
    # GIST index enables efficient ST_DWithin and ST_Distance operations
    op.execute("""
        CREATE INDEX idx_venues_location_gist 
        ON venues USING GIST (location)
    """)


def downgrade() -> None:
    """Downgrade schema to remove PostGIS location tracking."""
    # Drop the spatial index
    op.execute("DROP INDEX IF EXISTS idx_venues_location_gist")
    
    # Drop the location column
    op.execute("ALTER TABLE venues DROP COLUMN IF EXISTS location")
    
    # Note: We don't drop the PostGIS extension as other tables might use it
