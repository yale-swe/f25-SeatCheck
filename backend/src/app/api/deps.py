"""Shared dependencies for API endpoints."""

from typing import Generator
from sqlalchemy.orm import Session
from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session.

    Yields:
        Database session that will be automatically closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
