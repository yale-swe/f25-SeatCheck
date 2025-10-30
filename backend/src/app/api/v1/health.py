"""Health check endpoint."""

from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status and current timestamp
    """
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}
