-- backend/db/schema.sql
-- Assumes PostGIS extension already installed in the DB.
-- If not, run as superuser once: CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS venues (
  id         SERIAL PRIMARY KEY,
  name       TEXT NOT NULL,
  capacity   INTEGER NOT NULL DEFAULT 100 CHECK (capacity > 0),
  geom       GEOGRAPHY(POINT, 4326) NOT NULL,
  source     TEXT NOT NULL DEFAULT 'seed',
  ext_id     TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS venues_gix ON venues USING GIST ((geom::geometry));

CREATE TABLE IF NOT EXISTS checkins (
  id           BIGSERIAL PRIMARY KEY,
  netid        TEXT NOT NULL,
  venue_id     INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
  checkin_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  checkout_at  TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS checkins_user_active_idx  ON checkins(netid)   WHERE checkout_at IS NULL;
CREATE INDEX IF NOT EXISTS checkins_venue_active_idx ON checkins(venue_id) WHERE checkout_at IS NULL;

-- Optional: hard-enforce single active check-in per user
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relname = 'uniq_active_checkin_per_user'
  ) THEN
    EXECUTE 'CREATE UNIQUE INDEX uniq_active_checkin_per_user ON checkins(netid) WHERE checkout_at IS NULL;';
  END IF;
END$$;
