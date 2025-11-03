"""Database connection and session management."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,  # Log SQL queries if True
    pool_pre_ping=True,  # Verify connections before using them
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for all ORM models
class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session.

    Yields:
        Database session that will be automatically closed after use.

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
