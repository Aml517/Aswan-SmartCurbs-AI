from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.space import ParkingSpace
from app.models.occupancy import OccupancyLog
from app.schemas.occupancy import OccupancyUpdate


def process_occupancy_update(data: OccupancyUpdate, db: Session) -> OccupancyLog:
    """
    1. Find the parking space by space_id and zone_id.
    2. Update its status to the new value from the AI.
    3. Write a new record to occupancy_logs.
    4. Return the log entry so the API can respond with it.
    """

    # Step 1: Find the parking space
    space = db.query(ParkingSpace).filter(
        ParkingSpace.id == data.space_id,
        ParkingSpace.zone_id == data.zone_id
    ).first()

    if not space:
        raise HTTPException(
            status_code=404,
            detail=f"Space {data.space_id} not found in Zone {data.zone_id}."
        )

    # Step 2: Update the space status
    space.status = data.status
    space.last_updated = datetime.now(timezone.utc)

    # Step 3: Write a log entry
    log = OccupancyLog(
        zone_id=data.zone_id,
        space_id=data.space_id,
        status=data.status,
        confidence=data.confidence,
        source="ai_module"
    )
    db.add(log)

    # Commit both changes together
    db.commit()
    db.refresh(log)

    return log