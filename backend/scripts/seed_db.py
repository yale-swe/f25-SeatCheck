"""Seed database with initial Yale study venues."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.database import SessionLocal
from app.models import Venue

# Yale study venues
VENUES = [
    {
        "name": "Bass Library",
        "category": "library",
        "lat": 41.3083,
        "lon": -72.9289,
        "description": "Main undergraduate library with flexible study spaces",
        "capacity": 500,
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
        "verified": True,
    },
    {
        "name": "Sterling Memorial Library",
        "category": "library",
        "lat": 41.3102,
        "lon": -72.9276,
        "description": "Gothic cathedral-style library, quiet study atmosphere",
        "capacity": 800,
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
        "verified": True,
    },
    {
        "name": "Marx Science and Social Science Library",
        "category": "library",
        "lat": 41.3107,
        "lon": -72.9265,
        "description": "Science library with collaborative workspaces",
        "capacity": 300,
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
        "verified": True,
    },
]


def seed_venues():
    """Add initial Yale venues to database."""
    db = SessionLocal()
    try:
        # Check if venues already exist
        existing_count = db.query(Venue).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} venues. Skipping seed.")
            return

        # Add venues
        for venue_data in VENUES:
            venue = Venue(**venue_data)
            db.add(venue)

        db.commit()
        print(f"Successfully seeded {len(VENUES)} venues!")

        # Display added venues
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
