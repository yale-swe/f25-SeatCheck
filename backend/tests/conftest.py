import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def mock_db_session():
    """Create a mock database session that returns mock data."""

    from datetime import datetime, timezone

    mock_session = MagicMock()

    # Store state for check-ins and ratings

    checkins_data = {}

    ratings_data = []

    venue_exists = {1, 2}  # Mock venue IDs

    # Mock execute to return proper results

    def mock_execute(query, params=None, *args, **kwargs):
        result = MagicMock()

        result.rowcount = 0

        # Convert query to string for pattern matching

        query_str = str(query).upper()

        # Merge params into kwargs for easier access

        if params:
            kwargs.update(params)

        # Mock venue queries

        if "SELECT" in query_str and "VENUES" in query_str:
            if "GEOM" in query_str or "ST_" in query_str:
                # GeoJSON or geographic query

                result.fetchall.return_value = [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-72.9267, 41.3111],
                        },
                        "properties": {
                            "id": 1,
                            "name": "Test Library",
                            "capacity": 100,
                        },
                    }
                ]

            elif "WHERE" in query_str and "ID" in query_str:
                # Query by specific venue ID

                # Extract venue ID from query or params

                venue_id = kwargs.get("venue_id", 1)

                if venue_id in venue_exists:
                    result.fetchone.return_value = {
                        "id": venue_id,
                        "name": "Test Library",
                        "capacity": 100,
                        "lat": 41.3111,
                        "lon": -72.9267,
                        "availability": 0.7,
                        "avg_occupancy": 2.5,
                        "avg_noise": 1.5,
                        "recent_count": 3,
                    }

                    result.mappings.return_value.one_or_none.return_value = {
                        "id": venue_id,
                        "name": "Test Library",
                        "capacity": 100,
                        "lat": 41.3111,
                        "lon": -72.9267,
                        "availability": 0.7,
                        "avg_occupancy": 2.5,
                        "avg_noise": 1.5,
                        "recent_count": 3,
                    }

                else:
                    result.fetchone.return_value = None

                    result.mappings.return_value.one_or_none.return_value = None

            else:
                # Basic venue query - list all

                result.fetchall.return_value = [
                    {
                        "id": 1,
                        "name": "Test Library",
                        "capacity": 100,
                        "lat": 41.3111,
                        "lon": -72.9267,
                        "availability": 0.7,
                        "avg_occupancy": 2.5,
                        "avg_noise": 1.5,
                        "recent_count": 3,
                    },
                    {
                        "id": 2,
                        "name": "Test Study Hall",
                        "capacity": 50,
                        "lat": 41.3112,
                        "lon": -72.9268,
                        "availability": 0.8,
                        "avg_occupancy": 1.5,
                        "avg_noise": 0.5,
                        "recent_count": 1,
                    },
                ]

                result.mappings.return_value.all.return_value = (
                    result.fetchall.return_value
                )

        # Mock INSERT check-in queries

        elif "INSERT" in query_str and "CHECKINS" in query_str:
            # Extract data from query params

            venue_id = kwargs.get("venue_id", 1)

            netid = kwargs.get("netid", "testuser")

            if venue_id not in venue_exists:
                # Venue doesn't exist

                result.rowcount = 0

                result.mappings.return_value.one_or_none.return_value = None

            else:
                # Create check-in

                checkins_data[netid] = {
                    "id": len(checkins_data) + 1,
                    "venue_id": venue_id,
                    "checkin_at": datetime.now(timezone.utc).isoformat(),
                    "last_seen_at": datetime.now(timezone.utc).isoformat(),
                    "checkout_at": None,
                }

                result.rowcount = 1

                result.mappings.return_value.one_or_none.return_value = checkins_data[
                    netid
                ]

        # Mock INSERT rating queries

        elif "INSERT" in query_str and "RATINGS" in query_str:
            venue_id = kwargs.get("venue_id", 1)

            # Create rating regardless of venue existence (no FK validation in mock)

            rating_data = {
                "id": len(ratings_data) + 1,
                "venue_id": venue_id,
                "occupancy": kwargs.get("occupancy"),
                "noise": kwargs.get("noise"),
                "anonymous": kwargs.get("anonymous", True),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

            ratings_data.append(rating_data)

            # Create a row-like object with attribute access

            class Row:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)

            result.rowcount = 1

            result.first.return_value = Row(rating_data)

            result.mappings.return_value.one.return_value = rating_data

        # Mock UPDATE check-in queries (heartbeat and checkout)

        elif "UPDATE" in query_str and "CHECKINS" in query_str:
            # By default, no active check-in (returns None)

            result.rowcount = 0

            result.fetchone.return_value = None

            result.mappings.return_value.one_or_none.return_value = None

        # Mock SELECT check-in queries

        elif "SELECT" in query_str and "CHECKINS" in query_str:
            if "WHERE" in query_str:
                # Query for specific check-in

                result.fetchone.return_value = None

                result.mappings.return_value.one_or_none.return_value = None

            else:
                # Query for counts

                result.fetchall.return_value = [
                    {"venue_id": 1, "count": 3},
                    {"venue_id": 2, "count": 1},
                ]

                result.mappings.return_value.all.return_value = (
                    result.fetchall.return_value
                )

        else:
            result.fetchall.return_value = []

            result.fetchone.return_value = None

        return result

    mock_session.execute.side_effect = mock_execute

    mock_session.commit.return_value = None

    mock_session.rollback.return_value = None

    mock_session.close.return_value = None

    return mock_session


@pytest.fixture(scope="session")
def client(mock_db_session):
    """Provide a TestClient for the FastAPI app with mocked database."""

    # Create a mock SessionLocal class that returns our mock session
    class MockSessionLocal:
        def __call__(self):
            return mock_db_session

        def __enter__(self):
            return mock_db_session

        def __exit__(self, *args):
            pass

    mock_session_local = MockSessionLocal()
    # Patch SessionLocal in the main module to use our mock
    with patch("app.main.SessionLocal", mock_session_local):
        yield TestClient(app)


@pytest.fixture
def authenticated_client(client):
    """Provide an authenticated client using dev login."""
    # Call dev login to set session cookie
    client.get("/auth/dev/login")
    # Ensure any existing active checkin for the dev user is cleared so tests start clean
    try:
        client.post("/api/v1/checkins/checkout")
    except Exception:
        # ignore any errors here; it's best-effort to leave a clean state
        pass
    # The response should set a session cookie
    return client
