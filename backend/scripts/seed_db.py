""" "Seed database with initial Yale study venues."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import func
from app.database import SessionLocal
from app.models import Venue

# Yale study venues
VENUES = [
    {
        "name": "Bass Library",
        "category": "library",
        "lat": 41.3109,
        "lon": -72.9287,
        "description": "Main undergraduate library with flexible study spaces",
        "capacity": 400,
        "amenities": ["WiFi", "Power outlets", "Printing", "Group study rooms"],
        "accessibility": ["Wheelchair accessible", "Elevator"],
        "opening_hours": {
            "mon": "08:30-02:00",
            "tue": "08:30-02:00",
            "wed": "08:30-02:00",
            "thu": "08:30-02:00",
            "fri": "08:30-22:00",
            "sat": "10:00-22:00",
            "sun": "10:00-02:00",
        },
        "image_url": "/static/venues/bass_library.jpg",
        "verified": True,
    },
    {
        "name": "Sterling Memorial Library",
        "category": "library",
        "lat": 41.3102,
        "lon": -72.9276,
        "description": "Gothic cathedral-style library, quiet study atmosphere",
        "capacity": 500,
        "amenities": [
            "WiFi",
            "Power outlets",
            "Silent study areas",
            "Research collections",
        ],
        "accessibility": ["Wheelchair accessible", "Elevator"],
        "opening_hours": {
            "mon": "08:30-00:00",
            "tue": "08:30-00:00",
            "wed": "08:30-00:00",
            "thu": "08:30-00:00",
            "fri": "08:30-17:00",
            "sat": "10:00-17:00",
            "sun": "12:00-00:00",
        },
        "image_url": "/static/venues/sterling_memorial_library.jpg",
        "verified": True,
    },
    {
        "name": "Marx Science and Social Science Library",
        "category": "library",
        "lat": 41.3083,
        "lon": -72.9166,
        "description": "Science library with collaborative workspaces",
        "capacity": 200,
        "amenities": ["WiFi", "Power outlets", "Group study spaces", "Whiteboards"],
        "accessibility": ["Wheelchair accessible", "Elevator"],
        "opening_hours": {
            "mon": "08:30-22:00",
            "tue": "08:30-22:00",
            "wed": "08:30-22:00",
            "thu": "08:30-22:00",
            "fri": "08:30-17:00",
            "sat": "10:00-17:00",
            "sun": "12:00-22:00",
        },
        "image_url": "/static/venues/marx_library.jpg",
        "verified": True,
    },
    {
        "name": "Divinity School Library",
        "category": "library",
        "lat": 41.3134,
        "lon": -72.9282,
        "description": "Quiet reading room with historical collections",
        "capacity": 120,
        "amenities": ["WiFi", "Power outlets", "Silent study", "Reading rooms"],
        "accessibility": ["Wheelchair accessible"],
        "opening_hours": {
            "mon": "08:30-22:00",
            "tue": "08:30-22:00",
            "wed": "08:30-22:00",
            "thu": "08:30-22:00",
            "fri": "08:30-17:00",
            "sat": "10:00-17:00",
            "sun": "12:00-22:00",
        },
        "image_url": "/static/venues/divinity_school_library.jpg",
        "verified": True,
    },
    # ------ Additional Venues You Want ------
    {
        "name": "Beinecke Plaza",
        "category": "outdoor",
        "lat": 41.31161,
        "lon": -72.92722,
        "description": "Central outdoor study and gathering space",
        "capacity": 999,
        "amenities": ["Outdoor seating"],
        "accessibility": ["Wheelchair accessible"],
        "opening_hours": {},
        "image_url": "/static/venues/beinecke_plaza.jpg",
        "verified": True,
    },
    {
        "name": "CEID (Becton Center)",
        "category": "study",
        "lat": 41.3144,
        "lon": -72.92528,
        "description": "Engineering makerspace and collaborative study area",
        "capacity": 180,
        "amenities": ["WiFi", "Power outlets", "Study tables"],
        "accessibility": ["Wheelchair accessible"],
        "opening_hours": {},
        "image_url": "/static/venues/ceid_becton_center.jpg",
        "verified": True,
    },
    {
        "name": "Good Life Center",
        "category": "study",
        "lat": 41.3121,
        "lon": -72.9289,
        "description": "Wellness-centered quiet study and relaxation space",
        "capacity": 50,
        "amenities": ["WiFi", "Power outlets"],
        "accessibility": ["Wheelchair accessible"],
        "opening_hours": {},
        "image_url": "/static/venues/goodlife_center.jpg",
        "verified": True,
    },
    {
        "name": "Haas Library",
        "category": "library",
        "lat": 41.3141,
        "lon": -72.9385,
        "description": "Art and architecture library",
        "capacity": 150,
        "amenities": ["WiFi", "Study tables"],
        "accessibility": ["Wheelchair accessible"],
        "opening_hours": {},
        "image_url": "/static/venues/haas_library.jpg",
        "verified": True,
    },
    {
        "name": "Humanities Quadrangle",
        "category": "study",
        "lat": 41.3112,
        "lon": -72.9257,
        "description": "Indoor and outdoor humanities study spaces",
        "capacity": 200,
        "amenities": ["WiFi", "Power outlets"],
        "accessibility": ["Wheelchair accessible"],
        "opening_hours": {},
        "image_url": "/static/venues/humanities_quadrangle.jpg",
        "verified": True,
    },
    {
        "name": "Linsly-Chittenden Hall",
        "category": "study",
        "lat": 41.3097,
        "lon": -72.9263,
        "description": "Popular humanities academic building with study nooks",
        "capacity": 120,
        "amenities": ["WiFi"],
        "accessibility": ["Wheelchair accessible"],
        "opening_hours": {},
        "image_url": "/static/venues/linsly_chittenden_hall.jpeg",
        "verified": True,
    },
    {
        "name": "TSAI City",
        "category": "study",
        "lat": 41.3088,
        "lon": -72.9269,
        "description": "Innovation hub with open seating",
        "capacity": 100,
        "amenities": ["WiFi", "Power outlets"],
        "accessibility": ["Wheelchair accessible"],
        "opening_hours": {},
        "image_url": "/static/venues/TSAI_city.jpg",
        "verified": True,
    },
    {
        "name": "Yale Law School Courtyard",
        "category": "outdoor",
        "lat": 41.3127,
        "lon": -72.9294,
        "description": "Outdoor courtyard with tables and seating",
        "capacity": 150,
        "amenities": ["Outdoor seating"],
        "accessibility": ["Wheelchair accessible"],
        "opening_hours": {},
        "image_url": "/static/venues/yale_law_school_courtyard.jpg",
        "verified": True,
    },
]


def seed_venues():
    """Add initial Yale venues to database."""
    db = SessionLocal()
    try:
        existing_count = db.query(Venue).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} venues. Skipping seed.")
            return

        # Valid SQLAlchemy columns
        allowed_fields = {col.name for col in Venue.__table__.columns}

        for venue_data in VENUES:
            # Extract fields that belong to Venue
            filtered = {k: v for k, v in venue_data.items() if k in allowed_fields}

            lat = venue_data.get("lat")
            lon = venue_data.get("lon")

            if lat is None or lon is None:
                raise ValueError(f"Venue {venue_data['name']} is missing lat/lon!")

            # Compute geom (geography point)
            geom = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

            filtered["geom"] = geom

            venue = Venue(**filtered)
            db.add(venue)

        db.commit()
        print(f"Successfully seeded {len(VENUES)} venues!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    db = SessionLocal()
    try:
        # If venues already exist, skip
        existing_count = db.query(Venue).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} venues. Skipping seed.")
            return

        # Get valid SQLAlchemy columns
        allowed_fields = {col.name for col in Venue.__table__.columns}

        for venue_data in VENUES:
            # Keep only the keys that belong to the Venue model
            filtered = {k: v for k, v in venue_data.items() if k in allowed_fields}
            venue = Venue(**filtered)
            db.add(venue)

        db.commit()
        print(f"Successfully seeded {len(VENUES)} venues!")
        for venue in VENUES:
            print(f"  - {venue['name']}")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    """Add initial Yale venues to database."""
    db = SessionLocal()
    try:
        existing_count = db.query(Venue).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} venues. Skipping seed.")
            return

        for venue_data in VENUES:
            venue = Venue(**venue_data)
            db.add(venue)

        db.commit()
        print(f"Successfully seeded {len(VENUES)} venues!")
        for venue in VENUES:
            print(f"  - {venue['name']} ({venue['category']})")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding database with Yale study venues...")
    seed_venues()
    print("Done!")
