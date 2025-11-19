from fastapi import APIRouter
from . import health, venues, ratings, checkins

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(
    venues.router, prefix="/venues", tags=["venues"]
)  # → /api/v1/venues
api_router.include_router(
    ratings.router, prefix="/ratings", tags=["ratings"]
)  # → /api/v1/ratings
api_router.include_router(
    checkins.router, prefix="/checkins", tags=["checkins"]
)  # → /api/v1/checkins
