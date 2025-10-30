"""SeatCheck API - Main application entry point.

A real-time Yale campus study spot tracker that helps students find available
study locations through crowd-sourced check-ins.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import settings, get_cors_origins

# Initialize FastAPI application
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Real-time study spot availability tracker for Yale campus",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routes
app.include_router(api_router)
