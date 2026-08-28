from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.zone import ParkingZone
from app.models.space import ParkingSpace
from app.schemas.zone import ZoneCreate, SpaceCreate
from app.schemas.space import ZoneAvailabilityResponse, ZoneAvailabilitySummary, SpaceStatusItem


def create_zone(data: ZoneCreate, db: Session) -> ParkingZone:
    """Create a new parking zone."""
    zone = ParkingZone(
        name=data.name,
        location=data.location,
        total_spaces=data.total_spaces,
        latitude=data.latitude,
        longitude=data.longitude
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


def get_all_zones(db: Session):
    """Return all parking zones."""
    return db.query(ParkingZone).all()


def get_zone_by_id(zone_id: int, db: Session) -> ParkingZone:
    """Return a single zone or raise 404."""
    zone = db.query(ParkingZone).filter(ParkingZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found.")
    return zone


def create_space(data: SpaceCreate, db: Session) -> ParkingSpace:
    """Add a new parking space to an existing zone."""
    # Make sure the zone exists first
    get_zone_by_id(data.zone_id, db)

    space = ParkingSpace(
        zone_id=data.zone_id,
        space_number=data.space_number
    )
    db.add(space)
    db.commit()
    db.refresh(space)
    return space


def get_zone_availability(zone_id: int, db: Session) -> ZoneAvailabilityResponse:
    """Calculate and return full availability for a specific zone."""
    zone = get_zone_by_id(zone_id, db)
    spaces = db.query(ParkingSpace).filter(ParkingSpace.zone_id == zone_id).all()

    available = sum(1 for s in spaces if s.status == "available")
    occupied = sum(1 for s in spaces if s.status == "occupied")
    reserved = sum(1 for s in spaces if s.status == "reserved")

    return ZoneAvailabilityResponse(
        zone_id=zone.id,
        zone_name=zone.name,
        location=zone.location,
        total_spaces=zone.total_spaces,
        available_count=available,
        occupied_count=occupied,
        reserved_count=reserved,
        spaces=[
            SpaceStatusItem(id=s.id, space_number=s.space_number, status=s.status)
            for s in spaces
        ]
    )


def get_all_zones_availability(db: Session):
    """Return a brief availability summary for every zone."""
    zones = db.query(ParkingZone).all()
    result = []

    for zone in zones:
        spaces = db.query(ParkingSpace).filter(ParkingSpace.zone_id == zone.id).all()

        available = sum(1 for s in spaces if s.status == "available")
        occupied = sum(1 for s in spaces if s.status == "occupied")
        reserved = sum(1 for s in spaces if s.status == "reserved")

        result.append(ZoneAvailabilitySummary(
            zone_id=zone.id,
            zone_name=zone.name,
            location=zone.location,
            total_spaces=zone.total_spaces,
            available_count=available,
            occupied_count=occupied,
            reserved_count=reserved
        ))

    return result