from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReservationCreate(BaseModel):
    """
    What Flutter sends to POST /api/v1/reservations.
    The driver picks a space and provides their info.
    """
    space_id: int
    driver_name: str
    vehicle_plate: str
    end_time: Optional[datetime] = None  # Optional — driver can set expected end time


class ReservationResponse(BaseModel):
    """
    What the backend returns after creating or reading a reservation.
    """
    id: int
    space_id: int
    driver_name: str
    vehicle_plate: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True