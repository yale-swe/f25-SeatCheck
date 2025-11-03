"""API v1 routes."""

from fastapi import APIRouter
from app.api.v1 import checkins, venues, health

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, tags=["health"])
api_router.include_router(checkins.router, prefix="/checkins", tags=["checkins"])
api_router.include_router(venues.router, prefix="/venues", tags=["venues"])
