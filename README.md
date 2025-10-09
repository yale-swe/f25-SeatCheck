# f25-SeatCheck

**Description**: A real-time Yale campus study spot tracker built with React Native (Expo), FastAPI, and PostgreSQL.

---

## Project Overview
SeatCheck is designed to help Yale students find the best study spots on campus—whether they’re looking for a quiet room in Sterling or a collaborative table in Bass. Inspired by a “Waze for studying,” SeatCheck uses student check-ins and campus data to generate a live heatmap of study areas, displaying occupancy, noise levels, and available amenities.

---

## Long-term Vision
- Real-time study spot maps with occupancy and noise data  
- Social features like friend lists and optional location sharing  
- Gamification with badges, leaderboards, and profile customization  
- Predictive analytics to recommend the best times and locations to study  
- Real-time updates about locations  

This README documents our chosen tech stack, repo structure, setup instructions, current functionality, and future roadmap.

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

### Frontend
- **React Native with Expo** → Cross-platform mobile interface (iOS + Android)  
- **react-native-maps + Google Maps API** → Geospatial visualization + location services  
- **TypeScript** → Type safety and maintainability  

### Backend
- **FastAPI** → Asynchronous Python web framework  
- **RESTful endpoints** for locations, check-ins, and analytics  
- Built-in interactive API docs via Swagger (`/docs`)  
- **Google Maps Web APIs proxying** for Places, Geocoding, and Directions (keys secured)  

### Database
- **PostgreSQL** → Relational database for structured study spot data  
- Stores locations, user check-ins, occupancy levels, and noise  
- **PostGIS extension** → Enables geospatial queries (e.g., nearby locations, clustering)  

### Authentication
- **Yale CAS (Central Authentication Service)** planned for secure student logins  
- Current skeleton includes a placeholder login screen  
- Future: CAS gateway issues JWTs for authenticated API access  

### Real-Time Updates
- **WebSockets (FastAPI)** → Broadcasts new check-ins and updates to all clients  
- Powers live occupancy heatmaps  

---

## Repository Structure

---

### 1. **Backend (`backend/`)**
- **Purpose**: Establishes the Python backend foundation.

- **Key Files & Configuration**:  
  - **`.pre-commit-config.yaml`** → Runs automatic checks before every commit:
    - `ruff-check` and `ruff-format` for linting and code formatting
    - `trailing-whitespace` and `end-of-file-fixer` to clean file endings  
    - `mypy` for strict type checking (`uv run mypy --pretty --strict src`)  
  - **`pyproject.toml`** → Defines project metadata, Python version (≥3.12), and development dependencies (`mypy`, `pytest`, `pre-commit`) for reproducibility.  
  - **`main.py`** → Minimal executable script printing `"hello"`; serves as a placeholder for the future FastAPI entry point.  
  - **`tests/test_example.py`** → Sample `pytest` file confirming that unit testing and environment setup work correctly.  

- **Functionality**:  
  - Provides automated linting, formatting, and type checking for all backend code.  
  - Enables easy test writing and validation through `pytest`.  
  - Ensures consistent standards across all developer environments.  

- **Usage**:  
  1. Navigate to the backend directory → `cd backend`  
  2. Install dependencies → `uv sync` *(or `pip install -r requirements.txt`)*  
  3. Enable pre-commit hooks → `pre-commit install`  
  4. Run type checks → `uv run mypy --pretty --strict src`  
  5. Run tests → `pytest`  
  6. Execute backend script → `python main.py`  

---

### 2. **Mobile Application (`f25-SeatCheck/seat-check/`)**
- **Purpose**: Houses the React Native (Expo) mobile app.  
- **Key Directories**:
  - `app/` → Screens, layouts, navigation  
  - `components/` → Reusable UI blocks  
  - `constants/` → Centralized configs (themes, etc.)  
  - `hooks/` → Custom React hooks  
  - `assets/` → Images and static resources  
  - `scripts/` → Dev utilities  
- Follows React Native conventions; separates presentation, logic, and configs.  

---

### 3. **Root (`README.md`)**
- Provides project overview + onboarding instructions.  
- Keeps high-level docs accessible for new contributors.  
---

