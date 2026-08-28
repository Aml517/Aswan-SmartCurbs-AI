from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.schemas.zone import ZoneCreate, ZoneResponse, SpaceCreate, SpaceResponse
from app.services.zone_service import create_zone, get_all_zones, get_zone_by_id, create_space

router = APIRouter()


@router.post("/zones", response_model=ZoneResponse)
def add_zone(data: ZoneCreate, db: Session = Depends(get_db)):
    """
    Create a new parking zone.
    Use this via Swagger to seed demo data before the presentation.
    """
    return create_zone(data, db)


@router.get("/zones", response_model=List[ZoneResponse])
def list_zones(db: Session = Depends(get_db)):
    """
    Return all parking zones.
    Consumed by the Web Dashboard and Flutter app.
    """
    return get_all_zones(db)


@router.get("/zones/{zone_id}", response_model=ZoneResponse)
def get_zone(zone_id: int, db: Session = Depends(get_db)):
    """Return a single parking zone by ID."""
    return get_zone_by_id(zone_id, db)


@router.post("/zones/{zone_id}/spaces", response_model=SpaceResponse)
def add_space(zone_id: int, data: SpaceCreate, db: Session = Depends(get_db)):
    """
    Add a parking space to a zone.
    Use this via Swagger to seed demo spaces before the presentation.
    """
    # Force the zone_id from the URL path (ignore any zone_id in the body)
    data.zone_id = zone_id
    return create_space(data, db)