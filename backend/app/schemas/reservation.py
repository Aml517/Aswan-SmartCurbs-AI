from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReservationCreate(BaseModel):
    """
    Driver picks a space and provides their info.
    """
    space_id: int
    driver_name: str
    driver_email: Optional[str] = None
    driver_phone: Optional[str] = None
    vehicle_plate: str
    vehicle_model: Optional[str] = None
    start_time: Optional[datetime] = None  # Driver can set requested start time
    end_time: Optional[datetime] = None    # Driver can set requested end time
    duration_minutes: Optional[int] = None # Or provide duration in minutes


class ReservationResponse(BaseModel):
    """
    What the backend returns after creating or reading a reservation.
    """
    id: int
    space_id: int
    driver_name: str
    driver_email: Optional[str] = None
    driver_phone: Optional[str] = None
    vehicle_plate: str
    vehicle_model: Optional[str] = None
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True