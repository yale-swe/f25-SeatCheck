-- SeatCheck Database Schema
-- Assumes PostGIS extension already installed.

-- If not, run once as superuser:
--   CREATE EXTENSION IF NOT EXISTS postgis;

-- Venues Table
CREATE TABLE IF NOT EXISTS venues (
  id         SERIAL PRIMARY KEY,
  name       TEXT NOT NULL,
  capacity   INTEGER NOT NULL DEFAULT 100 CHECK (capacity > 0),
  geom       GEOGRAPHY(POINT, 4326) NOT NULL,  -- latitude/longitude
  source     TEXT NOT NULL DEFAULT 'seed',      -- e.g., 'seed', 'osm', 'manual'
  ext_id     TEXT,                              -- external ref (e.g., osm:way:12345)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Geospatial index for proximity/containment queries
CREATE INDEX IF NOT EXISTS venues_gix
  ON venues USING GIST ((geom::geometry));

-- Enforce unique venue names (optional but helps keep data clean)
CREATE UNIQUE INDEX IF NOT EXISTS venues_name_uidx ON venues (name);


-- Trigger: auto-update updated_at on row modification
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_venues_updated_at ON venues;
CREATE TRIGGER trg_venues_updated_at
BEFORE UPDATE ON venues
FOR EACH ROW EXECUTE FUNCTION set_updated_at();


-- Presence Check-Ins
-- Tracks who is currently present in each venue (one active per user).
CREATE TABLE IF NOT EXISTS checkins (
  id           BIGSERIAL PRIMARY KEY,
  netid        TEXT NOT NULL,
  venue_id     INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
  checkin_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  checkout_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS checkins_user_active_idx
  ON checkins(netid) WHERE checkout_at IS NULL;

CREATE INDEX IF NOT EXISTS checkins_venue_active_idx
  ON checkins(venue_id) WHERE checkout_at IS NULL;

-- Enforce single active check-in per user
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relname = 'uniq_active_checkin_per_user'
  ) THEN
    EXECUTE 'CREATE UNIQUE INDEX uniq_active_checkin_per_user
             ON checkins(netid)
             WHERE checkout_at IS NULL;';
  END IF;
END$$;


-- Crowd-Sourced Ratings (Anonymous)
-- Users can anonymously rate crowd level and noise level.
CREATE TABLE IF NOT EXISTS checkins_ratings (
  id           BIGSERIAL PRIMARY KEY,
  venue_id     INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
  occupancy    INTEGER NOT NULL CHECK (occupancy BETWEEN 0 AND 5),
  noise        INTEGER NOT NULL CHECK (noise BETWEEN 0 AND 5),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS checkins_ratings_venue_time_idx
  ON checkins_ratings(venue_id, created_at DESC);


-- Optional Convenience View: venues with lat/lon columns
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

