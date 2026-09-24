from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.space import ZoneAvailabilityResponse, ZoneAvailabilitySummary
from app.services.zone_service import get_zone_availability, get_all_zones_availability

router = APIRouter()


@router.get("/availability", response_model=List[ZoneAvailabilitySummary])
def get_all_availability(db: Session = Depends(get_db)):
    """
    Returns availability summary for ALL zones.
    Used by Web Dashboard for the overview map.
    Used by Flutter to show which zones have free spaces.
    """
    return get_all_zones_availability(db)


@router.get("/availability/{zone_id}", response_model=ZoneAvailabilityResponse)
def get_zone_availability_by_id(zone_id: int, db: Session = Depends(get_db)):
    """
    Returns full availability detail for ONE zone including every space status.
    Used by Flutter when a driver selects a specific zone.
    """
    return get_zone_availability(zone_id, db)