from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.occupancy import OccupancyUpdate, OccupancyResponse
from app.services.occupancy_service import process_occupancy_update
from app.models.occupancy import OccupancyLog

router = APIRouter()


@router.post("/occupancy", response_model=OccupancyResponse)
def update_occupancy(data: OccupancyUpdate, db: Session = Depends(get_db)):
    """
    Called by the AI module after every vehicle detection.

    Example request body:
    {
        "zone_id": 1,
        "space_id": 3,
        "status": "occupied",
        "confidence": 0.94
    }
    """
    log = process_occupancy_update(data, db)

    return OccupancyResponse(
        message="Occupancy updated successfully.",
        space_id=log.space_id,
        new_status=log.status,
        confidence=log.confidence,
        logged_at=log.created_at
    )


@router.get("/occupancy/logs")
def get_occupancy_logs(limit: int = 20, db: Session = Depends(get_db)):
    """
    Returns the most recent occupancy log entries.
    Used by the Web Dashboard to display detection history.
    """
    logs = db.query(OccupancyLog).order_by(
        OccupancyLog.created_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": log.id,
            "zone_id": log.zone_id,
            "space_id": log.space_id,
            "status": log.status,
            "confidence": log.confidence,
            "source": log.source,
            "created_at": log.created_at
        }
        for log in logs
    ]