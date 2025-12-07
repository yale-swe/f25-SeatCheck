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
- **pytest** → test runner (see [backend/tests/README.md](backend/tests/README.md) for testing documentation)
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

```
f25-SeatCheck/
├── backend/
│   ├── alembic/              # Migration environment + versions
│   ├── src/
│   │   └── app/
│   │       ├── api/
│   │       │   ├── auth.py   # Authentication endpoints
│   │       │   ├── deps.py   # FastAPI dependencies
│   │       │   └── v1/       # Versioned API endpoints
│   │       │       ├── checkins.py
│   │       │       ├── health.py
│   │       │       ├── ratings.py
│   │       │       └── venues.py
│   │       ├── crud/         # Database CRUD operations
│   │       ├── schemas/      # Pydantic request/response schemas
│   │       ├── services/     # Metrics + business logic
│   │       ├── database.py   # Engine, SessionLocal, Base
│   │       ├── config.py     # Pydantic settings
│   │       ├── models.py      # SQLAlchemy ORM models
│   │       └── main.py       # FastAPI entrypoint
│   ├── static/               # Static files (venue images)
│   ├── scripts/               # Utility scripts (seed_db.py)
│   ├── tests/                 # Test files
│   ├── pyproject.toml         # FastAPI + dev tools configuration
│   └── .pre-commit-config.yaml
│
└── seat-check/
    ├── app/                   # Expo Router navigation + screens
    │   ├── (tabs)/            # Tab-based navigation screens
    │   ├── login.tsx
    │   └── _layout.tsx
    ├── components/            # Shared UI components
    ├── constants/             # API constants and helpers
    ├── hooks/                 # React hooks
    ├── services/              # Business logic (MultiArmedBandit)
    ├── theme/                 # Theme provider and hooks
    ├── tests/                 # Vitest test files
    ├── assets/                # Images and static assets
    ├── package.json
    └── tsconfig.json
```


- **To run Seat-Check Locally**:

  Start all services (database, backend, and frontend) with Docker Compose:

  First, ensure that the docker desktop app is running.

  Then, run a following command.
  ```bash
  docker compose up
  ```

  This will start:
  - PostgreSQL database with PostGIS (port 5432)
  - FastAPI backend (port 8000)
  - Expo frontend (port 8081)

  The backend will automatically run migrations and seed the database on startup.

  Access the application at:
  - Frontend: http://localhost:8081
  - Backend API: http://localhost:8000
  - API Docs: http://localhost:8000/docs

  To stop all services:
  ```bash
  docker compose down
  ```


## Metrics Milestone: Multi-Armed Bandit Button Testing

We implemented a Multi-Armed Bandit algorithm to optimize the check-in button on our Check-In page.

**Implementation:**
* **Target:** Submit button on Check-In screen (`seat-check/app/(tabs)/checkin.tsx`)
* **3 Variants:** Blue button ("Submit check-in"), Green button ("Check In Now"), Orange button ("Submit")
* **Algorithm:** Epsilon-greedy Multi-Armed Bandit - shows all variants equally at first, then increasingly favors the best-performing one based on click-through rate
* **Tracking:** Records impressions (views) and conversions (clicks) in browser localStorage

**Files:**
* `seat-check/services/MultiArmedBanditService.ts` - Core algorithm
* `seat-check/app/(tabs)/checkin.tsx` - Integration
