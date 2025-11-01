"""Test script to verify PostGIS functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.database import SessionLocal
from app.crud import venues as crud_venues


def test_nearby_venues():
    """Test finding nearby venues."""
    print("\n=== Testing Nearby Venues ===")
    db = SessionLocal()
    try:
        # Bass Library coordinates
        lat, lon = 41.3083, -72.9289
        
        print(f"Searching for venues within 1km of ({lat}, {lon})...")
        results = crud_venues.get_nearby_venues(
            db=db,
            latitude=lat,
            longitude=lon,
            radius_meters=1000,
            limit=10
        )
        
        if not results:
            print("No venues found (database might be empty)")
            return False
        
        print(f"Found {len(results)} venues:")
        for venue, distance in results:
            print(f"  - {venue.name}: {distance:.0f}m away")
        
        return True
    finally:
        db.close()


def test_nearest_venue():
    """Test finding nearest venue."""
    print("\n=== Testing Nearest Venue ===")
    db = SessionLocal()
    try:
        # Random point near Yale
        lat, lon = 41.31, -72.93
        
        print(f"Finding nearest venue to ({lat}, {lon})...")
        result = crud_venues.get_nearest_venue(db=db, latitude=lat, longitude=lon)
        
        if not result:
            print("No venues found (database might be empty)")
            return False
        
        venue, distance = result
        print(f"Nearest venue: {venue.name} ({distance:.0f}m away)")
        return True
    finally:
        db.close()


def test_bounding_box():
    """Test bounding box query."""
    print("\n=== Testing Bounding Box Query ===")
    db = SessionLocal()
    try:
        # Box around Yale campus
        min_lat, max_lat = 41.30, 41.32
        min_lon, max_lon = -72.94, -72.92
        
        print(f"Finding venues in box: ({min_lat},{min_lon}) to ({max_lat},{max_lon})...")
        venues = crud_venues.get_venues_in_bounding_box(
            db=db,
            min_lat=min_lat,
            max_lat=max_lat,
            min_lon=min_lon,
            max_lon=max_lon
        )
        
        if not venues:
            print("No venues found in bounding box")
            return False
        
        print(f"Found {len(venues)} venues in box:")
        for venue in venues:
            print(f"  - {venue.name} at ({venue.lat}, {venue.lon})")
        
        return True
    finally:
        db.close()


def test_get_all_venues():
    """Test getting all venues."""
    print("\n=== Testing Get All Venues ===")
    db = SessionLocal()
    try:
        venues = crud_venues.get_all_venues(db=db, limit=100)
        
        if not venues:
            print("No venues in database")
            return False
        
        print(f"Found {len(venues)} venues in database")
        for venue in venues[:5]:  # Show first 5
            print(f"  - {venue.name} ({venue.category})")
        if len(venues) > 5:
            print(f"  ... and {len(venues) - 5} more")
        
        return True
    finally:
        db.close()


def check_postgis_extension():
    """Check if PostGIS extension is enabled."""
    print("\n=== Checking PostGIS Extension ===")
    db = SessionLocal()
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT PostGIS_version();")).scalar()
        print(f"PostGIS version: {result}")
        return True
    except Exception as e:
        print(f"PostGIS not available: {e}")
        print("\nTo fix this, run:")
        print("  psql -d seatcheck -c 'CREATE EXTENSION postgis;'")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("PostGIS Functionality Test")
    print("=" * 60)
    
    # Check PostGIS extension first
    postgis_ok = check_postgis_extension()
    
    if not postgis_ok:
        print("\nPostGIS extension is not enabled. Run migration first:")
        print("   uv run alembic upgrade head")
        sys.exit(1)
    
    # Run all tests
    tests = [
        ("Get All Venues", test_get_all_venues),
        ("Nearby Venues", test_nearby_venues),
        ("Nearest Venue", test_nearest_venue),
        ("Bounding Box", test_bounding_box),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\nAll tests passed! PostGIS is working correctly.")
    else:
        print("\nSome tests failed. Check the output above for details.")
        sys.exit(1)

