"""PostGIS integration tests.

Tests PostGIS database functionality using Docker database.
Requires: docker-compose up -d db
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1")).scalar()
        yield db
    except Exception as e:
        db.close()
        pytest.fail(
            f"Database connection failed. Is Docker running?\n"
            f"Run: docker-compose up -d db\n"
            f"Error: {e}"
        )
    finally:
        db.close()


def test_database_connection_uses_docker(db_session: Session):
    result = db_session.execute(text("""
        SELECT current_database(), current_user
    """)).first()
    
    db_name, db_user = result[0], result[1]
    
    assert db_name == "seatcheck"
    assert db_user == "seatcheck"
    
    postgis_version = db_session.execute(text("SELECT PostGIS_Version()")).scalar()
    assert postgis_version is not None


def test_postgis_extension_installed(db_session: Session):
    result = db_session.execute(text("SELECT PostGIS_Version()")).scalar()
    
    assert result is not None
    assert "USE_GEOS" in result or "GEOS" in result.upper()


def test_postgis_spatial_functions_available(db_session: Session):
    result = db_session.execute(text("""
        SELECT 
            ST_Y(ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geometry) AS lat,
            ST_X(ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geometry) AS lon
    """)).first()
    
    assert result is not None
    assert abs(result[0] - 41.3083) < 0.0001
    assert abs(result[1] - (-72.9289)) < 0.0001


def test_venues_table_has_geography_column(db_session: Session):
    result = db_session.execute(text("""
        SELECT 
            f_geography_column,
            type,
            srid
        FROM geography_columns
        WHERE f_table_name = 'venues' AND f_geography_column = 'geom'
    """)).first()
    
    assert result is not None
    assert result[0] == 'geom'
    assert result[1] == 'Point'
    assert result[2] == 4326


def test_geography_column_accepts_wgs84_coordinates(db_session: Session):
    try:
        db_session.execute(text("""
            INSERT INTO venues (name, capacity, geom, source)
            VALUES (
                'Test Venue',
                100,
                ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography,
                'test'
            )
        """))
        db_session.commit()
        
        result = db_session.execute(text("""
            SELECT name FROM venues WHERE name = 'Test Venue'
        """)).scalar()
        
        assert result == 'Test Venue'
        
        db_session.execute(text("DELETE FROM venues WHERE name = 'Test Venue'"))
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise


def test_st_y_st_x_extract_coordinates_from_venues(db_session: Session):
    db_session.execute(text("""
        INSERT INTO venues (name, capacity, geom, source)
        VALUES (
            'Bass Library Test',
            500,
            ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography,
            'test'
        )
    """))
    db_session.commit()
    
    try:
        result = db_session.execute(text("""
            SELECT 
                id,
                name,
                ST_Y(geom::geometry) AS lat,
                ST_X(geom::geometry) AS lon
            FROM venues
            WHERE name = 'Bass Library Test'
        """)).first()
        
        assert result is not None
        assert result[1] == 'Bass Library Test'
        assert abs(result[2] - 41.3083) < 0.0001
        assert abs(result[3] - (-72.9289)) < 0.0001
    finally:
        db_session.execute(text("DELETE FROM venues WHERE name = 'Bass Library Test'"))
        db_session.commit()


def test_venues_sql_query_pattern_works(db_session: Session):
    result = db_session.execute(text("""
        SELECT id, name, capacity,
               ST_Y(geom::geometry) AS lat,
               ST_X(geom::geometry) AS lon
        FROM venues
        ORDER BY name
        LIMIT 5
    """)).fetchall()
    
    assert len(result) >= 0
    
    if result:
        row = result[0]
        assert len(row) == 5
        assert isinstance(row[3], float)
        assert isinstance(row[4], float)


def test_gist_index_exists_on_venues_geom(db_session: Session):
    result = db_session.execute(text("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'venues' 
        AND indexdef LIKE '%gist%'
    """)).first()
    
    assert result is not None
    assert 'gist' in result[1].lower()
    assert 'geom' in result[1].lower() or 'geometry' in result[1].lower()


def test_st_dwithin_finds_nearby_venues(db_session: Session):
    db_session.execute(text("""
        INSERT INTO venues (name, capacity, geom, source) VALUES
        ('Near Venue', 100, ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography, 'test'),
        ('Far Venue', 100, ST_SetSRID(ST_MakePoint(-72.9500, 41.3300), 4326)::geography, 'test')
    """))
    db_session.commit()
    
    try:
        radius_meters = 1000
        
        result = db_session.execute(text("""
            SELECT name
            FROM venues
            WHERE ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(-72.9279, 41.3083), 4326)::geography,
                :radius
            )
            AND source = 'test'
        """), {"radius": radius_meters}).fetchall()
        
        venue_names = [row[0] for row in result]
        assert 'Near Venue' in venue_names
    finally:
        db_session.execute(text("DELETE FROM venues WHERE source = 'test'"))
        db_session.commit()


def test_st_distance_returns_meters_for_geography(db_session: Session):
    distance = db_session.execute(text("""
        SELECT ST_Distance(
            ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography,
            ST_SetSRID(ST_MakePoint(-72.9276, 41.3102), 4326)::geography
        )
    """)).scalar()
    
    assert distance is not None
    assert 100 < distance < 500


def test_st_distance_symmetric(db_session: Session):
    dist_ab = db_session.execute(text("""
        SELECT ST_Distance(
            ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography,
            ST_SetSRID(ST_MakePoint(-72.9276, 41.3102), 4326)::geography
        )
    """)).scalar()
    
    dist_ba = db_session.execute(text("""
        SELECT ST_Distance(
            ST_SetSRID(ST_MakePoint(-72.9276, 41.3102), 4326)::geography,
            ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography
        )
    """)).scalar()
    
    assert abs(dist_ab - dist_ba) < 0.01


def test_nearest_venue_using_knn_operator(db_session: Session):
    db_session.execute(text("""
        INSERT INTO venues (name, capacity, geom, source) VALUES
        ('Nearest', 100, ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography, 'test'),
        ('Farther', 100, ST_SetSRID(ST_MakePoint(-72.9500, 41.3300), 4326)::geography, 'test')
    """))
    db_session.commit()
    
    try:
        result = db_session.execute(text("""
            SELECT name
            FROM venues
            WHERE source = 'test'
            ORDER BY geom <-> ST_SetSRID(ST_MakePoint(-72.9288, 41.3084), 4326)::geography
            LIMIT 1
        """)).scalar()
        
        assert result == 'Nearest'
    finally:
        db_session.execute(text("DELETE FROM venues WHERE source = 'test'"))
        db_session.commit()


def test_zero_distance_to_same_point(db_session: Session):
    distance = db_session.execute(text("""
        SELECT ST_Distance(
            ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography,
            ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography
        )
    """)).scalar()
    
    assert distance == 0.0


def test_st_dwithin_with_zero_radius_matches_exact_location(db_session: Session):
    db_session.execute(text("""
        INSERT INTO venues (name, capacity, geom, source)
        VALUES ('Exact Match', 100, 
                ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography, 'test')
    """))
    db_session.commit()
    
    try:
        exact = db_session.execute(text("""
            SELECT COUNT(*)
            FROM venues
            WHERE ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography,
                0
            )
            AND source = 'test'
        """)).scalar()
        
        assert exact == 1
        
        nearby = db_session.execute(text("""
            SELECT COUNT(*)
            FROM venues
            WHERE ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(-72.9288, 41.3084), 4326)::geography,
                0
            )
            AND source = 'test'
        """)).scalar()
        
        assert nearby == 0
    finally:
        db_session.execute(text("DELETE FROM venues WHERE source = 'test'"))
        db_session.commit()


def test_find_venues_within_walking_distance(db_session: Session):
    db_session.execute(text("""
        INSERT INTO venues (name, capacity, geom, source) VALUES
        ('Close', 100, ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography, 'test'),
        ('Medium', 100, ST_SetSRID(ST_MakePoint(-72.9295, 41.3088), 4326)::geography, 'test'),
        ('Far', 100, ST_SetSRID(ST_MakePoint(-72.9500, 41.3300), 4326)::geography, 'test')
    """))
    db_session.commit()
    
    try:
        results = db_session.execute(text("""
            SELECT name
            FROM venues
            WHERE ST_DWithin(
                geom,
                ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography,
                500
            )
            AND source = 'test'
            ORDER BY ST_Distance(geom, ST_SetSRID(ST_MakePoint(-72.9289, 41.3083), 4326)::geography)
        """)).fetchall()
        
        venue_names = [row[0] for row in results]
        assert 'Close' in venue_names
        assert 'Medium' in venue_names
        assert 'Far' not in venue_names
    finally:
        db_session.execute(text("DELETE FROM venues WHERE source = 'test'"))
        db_session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
