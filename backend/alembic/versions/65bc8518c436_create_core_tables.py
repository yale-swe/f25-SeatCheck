"""create core tables

Revision ID: 0001_core
Revises:
Create Date: 2025-11-05 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography

# revision identifiers, used by Alembic.
revision: str = "65bc8518c436"
down_revision: str | None = None  # base migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure PostGIS exists (safe if already installed)
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # venues
    op.create_table(
        "venues",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("capacity", sa.Integer, nullable=False, server_default="100"),
        sa.Column("geom", Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("source", sa.Text, nullable=False, server_default="seed"),
        sa.Column("ext_id", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    # unique name & spatial index (cast to geometry for GIST)
    op.create_index("venues_name_uidx", "venues", ["name"], unique=True)
    op.execute("CREATE INDEX venues_gix ON venues USING GIST ((geom::geometry))")

    # trigger for updated_at
    op.execute("""
    CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
    BEGIN
      NEW.updated_at = now();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
    op.execute("""
    CREATE TRIGGER trg_venues_updated_at
    BEFORE UPDATE ON venues
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)

    # presence check-ins (who is there now)
    op.create_table(
        "checkins",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("netid", sa.Text, nullable=False),
        sa.Column(
            "venue_id",
            sa.Integer,
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "checkin_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("checkout_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index(
        "checkins_user_active_idx",
        "checkins",
        ["netid"],
        postgresql_where=sa.text("checkout_at IS NULL"),
    )
    op.create_index(
        "checkins_venue_active_idx",
        "checkins",
        ["venue_id"],
        postgresql_where=sa.text("checkout_at IS NULL"),
    )
    # one active check-in per user
    op.create_index(
        "uniq_active_checkin_per_user",
        "checkins",
        ["netid"],
        unique=True,
        postgresql_where=sa.text("checkout_at IS NULL"),
    )

    # anonymous ratings (crowd + noise)
    op.create_table(
        "ratings",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "venue_id",
            sa.Integer,
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("occupancy", sa.Integer, nullable=False),
        sa.Column("noise", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("occupancy BETWEEN 0 AND 5", name="ratings_occupancy_range"),
        sa.CheckConstraint("noise BETWEEN 0 AND 5", name="ratings_noise_range"),
    )
    op.create_index("ratings_venue_time_idx", "ratings", ["venue_id", "created_at"])

    # convenience view with lat/lon (optional)
    op.execute("""
    CREATE OR REPLACE VIEW venues_ll AS
    SELECT
      id,
      name,
      capacity,
      ST_Y(geom::geometry) AS lat,
      ST_X(geom::geometry) AS lon,
      source,
      ext_id,
      created_at,
      updated_at
    FROM venues;
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS venues_ll")
    op.drop_index("ratings_venue_time_idx", table_name="ratings")
    op.drop_table("ratings")
    op.drop_index("uniq_active_checkin_per_user", table_name="checkins")
    op.drop_index("checkins_venue_active_idx", table_name="checkins")
    op.drop_index("checkins_user_active_idx", table_name="checkins")
    op.drop_table("checkins")
    op.execute("DROP TRIGGER IF EXISTS trg_venues_updated_at ON venues")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at")
    op.execute("DROP INDEX IF EXISTS venues_gix")
    op.drop_index("venues_name_uidx", table_name="venues")
    op.drop_table("venues")
