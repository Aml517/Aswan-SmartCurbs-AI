from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.reservation import Reservation
from app.models.space import ParkingSpace
from app.schemas.reservation import ReservationCreate


def create_reservation(data: ReservationCreate, db: Session) -> Reservation:
    """
    Create a new reservation for a parking space.
    - Checks the space exists and is available.
    - Creates the reservation record.
    - Updates the space status to "reserved".
    """

    # Step 1: Find the space
    space = db.query(ParkingSpace).filter(ParkingSpace.id == data.space_id).first()

    if not space:
        raise HTTPException(
            status_code=404,
            detail=f"Parking space {data.space_id} not found."
        )

    # Step 2: Validate zone policy (RESTRICTED zones cannot be reserved)
    zone = space.zone
    if zone and (zone.zone_type or "").upper() == "RESTRICTED":
        reason = zone.restriction_reason or "Public parking is prohibited in this restricted zone."
        raise HTTPException(
            status_code=400,
            detail=f"Parking space {data.space_id} is in a restricted zone ({reason}) and cannot be reserved."
        )

    # Step 3: Make sure the space is available
    if space.status != "available":
        raise HTTPException(
            status_code=400,
            detail=f"Space {data.space_id} is currently '{space.status}' and cannot be reserved."
        )

    # Step 3: Compute start and end times preserving local timestamps
    start_dt = data.start_time or datetime.now()
    if data.end_time:
        end_dt = data.end_time
    elif data.duration_minutes:
        end_dt = start_dt + timedelta(minutes=data.duration_minutes)
    else:
        end_dt = start_dt + timedelta(minutes=90)  # Default 1.5 hours

    reservation = Reservation(
        space_id=data.space_id,
        driver_name=data.driver_name,
        driver_email=data.driver_email,
        driver_phone=data.driver_phone,
        vehicle_plate=data.vehicle_plate,
        vehicle_model=data.vehicle_model or "Car — Sedan",
        status="active",
        start_time=start_dt,
        end_time=end_dt
    )
    db.add(reservation)

    # Step 4: Mark the space as reserved
    space.status = "reserved"

    db.commit()
    db.refresh(reservation)
    return reservation


def get_reservation(reservation_id: int, db: Session) -> Reservation:
    """Fetch a reservation by ID or raise 404."""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail=f"Reservation {reservation_id} not found."
        )
    return reservation


def cancel_reservation(reservation_id: int, db: Session) -> Reservation:
    """
    Cancel an active reservation.
    - Sets reservation status to "cancelled".
    - Frees the parking space back to "available".
    """
    reservation = get_reservation(reservation_id, db)

    if reservation.status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Reservation {reservation_id} is already '{reservation.status}'."
        )

    # Free the space
    space = db.query(ParkingSpace).filter(ParkingSpace.id == reservation.space_id).first()
    if space:
        space.status = "available"

    # Cancel the reservation
    reservation.status = "cancelled"

    db.commit()
    db.refresh(reservation)
    return reservation


def list_reservations(db: Session, skip: int = 0, limit: int = 50, status: str = None):
    """Fetch all reservations with optional status filter."""
    query = db.query(Reservation)
    if status:
        query = query.filter(Reservation.status == status)
    return query.order_by(Reservation.id.desc()).offset(skip).limit(limit).all()