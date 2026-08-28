from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.reservation import ReservationCreate, ReservationResponse
from app.services.reservation_service import create_reservation, get_reservation, cancel_reservation

router = APIRouter()


@router.post("/reservations", response_model=ReservationResponse)
def make_reservation(data: ReservationCreate, db: Session = Depends(get_db)):
    """
    Create a new reservation.
    Called by the Flutter Driver App when a driver books a space.

    Example request body:
    {
        "space_id": 1,
        "driver_name": "Ahmed Mohamed",
        "vehicle_plate": "ASW 1234"
    }
    """
    return create_reservation(data, db)


@router.get("/reservations/{reservation_id}", response_model=ReservationResponse)
def fetch_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a reservation by its ID.
    Flutter uses this to show the driver their active booking.
    """
    return get_reservation(reservation_id, db)


@router.patch("/reservations/{reservation_id}/cancel", response_model=ReservationResponse)
def cancel(reservation_id: int, db: Session = Depends(get_db)):
    """
    Cancel an active reservation.
    Frees the parking space back to available automatically.
    """
    return cancel_reservation(reservation_id, db)