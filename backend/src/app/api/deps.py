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
    # Try to get netid from session cookie first (for production)
    netid = request.session.get("netid")
    
    # If no session, try Authorization header (for dev token-based auth)
    if not netid:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                import base64
                import json
                # Add padding if needed
                token += "=" * (4 - len(token) % 4)
                token_data = json.loads(base64.urlsafe_b64decode(token).decode())
                if token_data.get("type") == "dev" and "netid" in token_data:
                    netid = token_data["netid"]
            except Exception:
                # Token decode failed, continue to check session
                pass
    
    if not netid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return str(netid)
