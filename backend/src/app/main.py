# backend/src/app/main.py
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from app.database import SessionLocal
from app.config import settings
from app.api.v1 import api_router as api_v1_router
from app.api import auth as auth_router


# --- Debug: log referer for any legacy callers hitting old paths -----------
class RefererLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.endswith("/with_occupancy"):
            ref = request.headers.get("referer", "-")
            ua = request.headers.get("user-agent", "-")
            print(f"[DEBUG] with_occupancy caller → referer={ref} ua={ua}")
        return response


# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    debug=settings.debug,
)


# --- DB dependency (needed by tests/mypy) -----------------------------------
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- CORS --------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Sessions ---------------------------------------------------------------
# For localhost development with different ports, we need same_site="none"
# Note: Some browsers require secure=True with same_site="none", but allow
# secure=False for localhost. If this doesn't work, we may need a custom handler.
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="seatcheck_session",
    same_site="none",  # Changed from "lax" to allow cross-origin cookies
    max_age=86400,  # 24 hours
)

# Debug logger for legacy callers
app.add_middleware(RefererLogMiddleware)

# --- Static files (for venue images, etc.) ----------------------------------
# Resolve backend/static relative to this file:
STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
print(
    f"[SeatCheck] Static dir resolved to: {STATIC_DIR} (exists={STATIC_DIR.exists()})"
)

if not STATIC_DIR.exists():
    # Fail loudly in dev if the static directory is wrong/missing
    raise RuntimeError(f"[SeatCheck] Static directory not found: {STATIC_DIR}")

# Mount /static so /static/venues/... is served from backend/static/venues/...
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Small debug endpoint to confirm what FastAPI sees
@app.get("/debug/static", tags=["debug"])
def debug_static():
    return {
        "static_dir": str(STATIC_DIR),
        "exists": STATIC_DIR.exists(),
    }


# --- Routers -----------------------------------------------------------------
# Auth (dev login / CAS hook)
app.include_router(auth_router.router, tags=["auth"])

# Versioned API
app.include_router(api_v1_router, prefix="/api/v1")


# --- Root ---------------------------------------------------------------------
@app.get("/", tags=["root"])
def root(request: Request):
    """Root endpoint - redirects to frontend or returns API info."""
    from fastapi.responses import RedirectResponse

    # If there's a token parameter (from dev login), return a simple response
    # to avoid redirect loops in tests
    if "token" in request.query_params:
        return {"status": "ok", "message": "Token received"}

    return RedirectResponse(url=settings.app_base, status_code=302)


# --- Health ------------------------------------------------------------------
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}
