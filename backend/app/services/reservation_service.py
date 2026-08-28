from datetime import datetime, timezone
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

    # Step 2: Make sure the space is available
    if space.status != "available":
        raise HTTPException(
            status_code=400,
            detail=f"Space {data.space_id} is currently '{space.status}' and cannot be reserved."
        )

    # Step 3: Create the reservation
    reservation = Reservation(
        space_id=data.space_id,
        driver_name=data.driver_name,
        vehicle_plate=data.vehicle_plate,
        status="active",
        start_time=datetime.now(timezone.utc),
        end_time=data.end_time
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