# backend/src/app/api/deps.py
from collections.abc import Generator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_login(request: Request) -> str:
    netid = request.session.get("netid")
    if not netid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return str(netid)
