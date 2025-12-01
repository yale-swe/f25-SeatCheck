# f25-SeatCheck

**Description**: A real-time Yale campus study-spot tracker built with React Native (Expo), FastAPI, PostgreSQL, and PostGIS.

---

## Project Overview

SeatCheck helps Yale students find their ideal study spaces on campus, using real-time student check-ins, noise ratings, and aggregated analytics. Designed as a “Waze for studying,” SeatCheck provides a live map of campus study areas, showing occupancy, noise levels, and when each space was last active.

---

## Long-term Vision

- Real-time occupancy + noise maps
- Optional friend lists and social location sharing
- Leaderboards and gamified study-streak features
- Predictive analytics for when spaces will be full
- Real-time updates about location congestion

This README documents the tech stack, repo structure, dev workflow, and future roadmap.

---

## Team Members

- **Snikitha Banda**
- **Kashvi Pundir**
- **David Cho**
- **Barsbold Enkhbold**
- **Adrian Hoang**
- **Cody Skinner**

---

## Tech Stack

### Frontend (seat-check/)

- **React Native (Expo router)** → Cross-platform mobile interface (iOS + Android)
- **TypeScript** → type-safe component logic
- **react-native-maps + Google Maps SDK** → Geospatial visualization of Yale
- Handles:
    map display
    check-ins / ratings UI
    current user location (permission-based)
    venue detail cards


### Backend (backend/src/app/)

- **FastAPI** → high-performance async backend
- **Alembic** → migrations for PostgreSQL/PostGIS
- **Pydantic v2** → request/response validation
- **Ruff** → linting + formatting
- **mypy** (strict) → static type checking
- **pytest** → test runner
- **Pre-commit** → automated formatting & lint guards
  REST endpoints include:
    POST /api/v1/ratings – occupancy/noise rating submission
    POST /api/v1/checkins – heartbeat, check-in, and check-out
    GET /api/v1/venues – venue metadata + geospatial info
    GET /api/v1/metrics – aggregated occupancy analytics

### Database

- **PostgreSQL** → Relational database for structured study spot data
    venues, check-ins, ratings, and aggregated analytics
- **PostGIS extension** → Enables geospatial queries (e.g., nearby locations, clustering)

### Authentication
- **Planned: Yale CAS authentication**

- **Current backend includes:**
- Session-based placeholder
- Require_login dependency

### Real-Time Updates

- **WebSockets** → Broadcasts new check-ins and updates to all clients

---

## General Repository Structure

---

f25-SeatCheck/
├── backend/
│   ├── alembic/              # Migration environment + versions
│   ├── src/
│   │   └── app/
│   │       ├── api/
│   │       │   └── v1/
│   │       ├── models/       # SQLAlchemy ORM models
│   │       ├── services/     # Metrics + business logic
│   │       ├── database.py   # Engine, SessionLocal, Base
│   │       ├── config.py     # Pydantic settings
│   │       └── main.py       # FastAPI entrypoint
│   ├── pyproject.toml        # FastAPI + dev tools configuration
│   ├── .pre-commit-config.yaml
│   └── tests/
│       └── ...
│
└── seat-check/
    ├── app/                  # Expo Router navigation + screens
    ├── components/           # Shared UI components
    ├── __tests__/            # Vitest test files
    ├── package.json
    └── tsconfig.json


- **To run SEATCHECK Locally**:
  Open 2 Terminal Windows.

  Complete the two setups:

    - **BACKEND SETUP**:
      Setup Project:
        cd backend
        .\.venv\Scripts\activate

      Check Postgres:
        net start postgresql-x64-18

      Run Server:
        uvicorn app.main:app --reload

      Run Type Checking:
        uv run mypy --pretty --strict src

      Run Tests:
        pytest


    - **Frontend SETUP**:
      Setup Project:
        cd seat-check
        npm install

      Run App:
        npx expo start

      Run Tests:
        npm test
