# backend/src/app/main.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.api.v1 import api_router as api_v1_router
from app.api import auth as auth_router


# --- debug: log referer for legacy callers hitting old paths ---
class RefererLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Helps find ANY stale caller still polling the old endpoint
        if request.url.path.endswith("/with_occupancy"):
            ref = request.headers.get("referer", "-")
            ua = request.headers.get("user-agent", "-")
            print(f"[DEBUG] with_occupancy caller → referer={ref} ua={ua}")
        return response


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    debug=settings.debug,
)
from app.db import SessionLocal

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(filename=".env"))

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------
app = FastAPI(title="SeatCheck API", version="0.1.0")

# ---- Frontend base ----------------------------------------------------------
APP_BASE = os.getenv("APP_BASE", "http://localhost:8081")

# ---- CORS -------------------------------------------------------------------
default_origins = [
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
]
extra_origins = (
    os.getenv("DEV_ORIGINS", "").split(",") if os.getenv("DEV_ORIGINS") else []
)
DEV_ORIGINS = list(set(default_origins + extra_origins))

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie="seatcheck_session",
    same_site="lax",
)

# Add debug referer logger AFTER app exists
app.add_middleware(RefererLogMiddleware)

# --- Static ---
STATIC_DIR = Path(__file__).resolve().parents[2] / "static"
print(f"[SeatCheck] Static dir resolved to: {STATIC_DIR}")
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# --- Routers ---
app.include_router(auth_router.router, tags=["auth"])
app.include_router(api_v1_router, prefix="/api/v1")


# --- Health ---
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}
