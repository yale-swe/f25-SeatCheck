# src/app/database.py
"""Database engine, session factory, and Base."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Single engine for the whole app
engine = create_engine(
    settings.database_url,  # e.g. "postgresql+psycopg2://user:pass@host:5432/db"
    echo=settings.database_echo,  # toggle SQL logging via config
    pool_pre_ping=True,  # validate connections before use
    future=True,  # 2.0-style engine behavior
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


# One (and only one) Declarative Base
class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# FastAPI dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        return (yield db)
    finally:
        db.close()
