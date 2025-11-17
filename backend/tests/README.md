# Backend Test Suite

This directory contains comprehensive test cases for the SeatCheck backend API.

## Test Coverage

The test suite includes:

- **test_auth.py** (15 tests) - Authentication endpoints including CAS login, dev login, logout, and session management
- **test_venues.py** (18 tests) - Venue-related endpoints including listing, occupancy metrics, GeoJSON, and stats
- **test_checkins.py** (20 tests) - Check-in presence endpoints for tracking active users
- **test_ratings.py** (23 tests) - Rating endpoints for crowd-sourced occupancy and noise data
- **test_health.py** (2 tests) - Health check and basic API functionality

**Total: 78 test cases**

## Running Tests

### Prerequisites

1. **Database Required**: Most tests require a running PostgreSQL database with PostGIS extension.

2. **Start the database** using docker-compose:
   ```bash
   # From the project root directory
   docker-compose up db -d
   ```

3. **Wait for database to be ready**:
   ```bash
   docker-compose exec db pg_isready -U seatcheck -d seatcheck
   ```

4. **Seed the database** (if not already done):
   ```bash
   cd backend
   uv run python scripts/seed_db.py
   ```

### Run All Tests

```bash
cd backend
uv run pytest tests/ -v
```

### Run Specific Test Files

```bash
# Test authentication endpoints
uv run pytest tests/test_auth.py -v

# Test venue endpoints
uv run pytest tests/test_venues.py -v

# Test check-in endpoints
uv run pytest tests/test_checkins.py -v

# Test rating endpoints
uv run pytest tests/test_ratings.py -v
```

### Run Tests Without Database

Some tests don't require a database (auth tests, validation tests):

```bash
# Run only tests that don't need database connections
uv run pytest tests/test_auth.py::test_dev_login_success -v
uv run pytest tests/test_auth.py::test_cas_login_redirect -v
```

## Test Configuration

Tests use the following configuration:

- **Test Client**: FastAPI's `TestClient` for HTTP requests
- **Authentication**: Dev auth mode with `/auth/dev/login` endpoint
- **Database**: Connects to PostgreSQL at `localhost:5432` (configurable via `DATABASE_URL` env var)
- **Session Management**: Server-side sessions with cookies

## Environment Variables

The following environment variables are used during testing (defaults from main app):

- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql+psycopg2://seatcheck:seatcheck@localhost:5432/seatcheck`)
- `DEV_AUTH` - Enable dev authentication (default: `"1"`)
- `APP_BASE` - Frontend base URL for redirects (default: `http://localhost:8081`)

## Test Structure

### Fixtures (conftest.py)

- `client` - Session-scoped TestClient for making HTTP requests
- `authenticated_client` - Authenticated client with dev login session

### Test Patterns

1. **Authentication Tests**: Verify login/logout flows, session persistence, CAS integration
2. **CRUD Tests**: Create, read, update operations for venues, check-ins, and ratings
3. **Validation Tests**: Input validation, error handling, edge cases
4. **Integration Tests**: Multi-step workflows (check-in lifecycle, multiple users)
5. **Data Consistency Tests**: Verify metrics calculations, timestamp handling

## Common Issues

### Database Connection Errors

```
sqlalchemy.exc.OperationalError: connection to server at "localhost", port 5432 failed
```

**Solution**: Start the database with `docker-compose up db -d`

### Too Many Redirects

If tests fail with `httpx.TooManyRedirects`, ensure `follow_redirects=False` is used when calling `/auth/dev/login`.

### Session Not Persisting

Make sure the `authenticated_client` fixture is being used, which properly sets up the session before making authenticated requests.

## Writing New Tests

When adding new tests:

1. Use `authenticated_client` fixture for endpoints that require authentication
2. Use `follow_redirects=False` when calling login endpoints
3. Add appropriate assertions for status codes and response structure
4. Test both success and failure cases
5. Include validation and edge case tests
6. Consider test isolation - tests should not depend on each other

Example:

```python
def test_my_endpoint(authenticated_client):
    """Test description."""
    response = authenticated_client.get("/my-endpoint")
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

## CI/CD Integration

To run tests in CI/CD pipelines:

1. Start PostgreSQL with PostGIS in a service container
2. Set `DATABASE_URL` environment variable
3. Run database migrations/seeding
4. Execute pytest

Example GitHub Actions:

```yaml
services:
  postgres:
    image: postgis/postgis:16-3.4
    env:
      POSTGRES_DB: seatcheck
      POSTGRES_USER: seatcheck
      POSTGRES_PASSWORD: seatcheck
    ports:
      - 5432:5432

steps:
  - name: Run tests
    env:
      DATABASE_URL: postgresql+psycopg2://seatcheck:seatcheck@localhost:5432/seatcheck
    run: |
      uv run python scripts/seed_db.py
      uv run pytest tests/ -v
```
