"""Check-in endpoints for venue reporting."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import User, Venue, CheckIn
from app.schemas.checkin import CheckInRequest, CheckInResponse

router = APIRouter()


@router.post("", response_model=CheckInResponse, status_code=201)
def create_checkin(
    checkin: CheckInRequest, db: Session = Depends(get_db)
) -> CheckInResponse:
    """Create a new check-in report for a venue.

    Records occupancy and noise levels at a specific venue.
    User ID is optional for MVP (will be required when auth is implemented).

    Args:
        checkin: Check-in data (venue_id, occupancy, noise, optional user_id)
        db: Database session

    Returns:
        Confirmation with check-in ID

    Raises:
        HTTPException: 404 if venue not found
    """
    # Verify venue exists
    venue = db.query(Venue).filter(Venue.id == checkin.venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=404, detail=f"Venue {checkin.venue_id} not found"
        )

    # For MVP: create a default user if user_id not provided
    user_id = checkin.user_id
    if user_id is None:
        # Get or create anonymous user
        anonymous_user = db.query(User).filter(User.netid == "anonymous").first()

        if not anonymous_user:
            anonymous_user = User(
                netid="anonymous",
                display_name="Anonymous User",
                anonymize_checkins=True,
            )
            db.add(anonymous_user)
            db.commit()
            db.refresh(anonymous_user)

        user_id = anonymous_user.id

    # Create check-in
    db_checkin = CheckIn(
        venue_id=checkin.venue_id,
        user_id=user_id,
        occupancy=checkin.occupancy,
        noise=checkin.noise,
        anonymous=True,  # Default to anonymous for now
    )

    db.add(db_checkin)
    db.commit()
    db.refresh(db_checkin)

    return CheckInResponse(ok=True, checkin_id=db_checkin.id)
