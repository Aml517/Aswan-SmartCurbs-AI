from pydantic import BaseModel
from typing import List, Optional


class SpaceStatusItem(BaseModel):
    """Represents a single parking space with its current status."""
    id: int
    space_number: str
    status: str  # "available", "occupied", or "reserved"

    class Config:
        from_attributes = True


class ZoneAvailabilityResponse(BaseModel):
    """
    Full availability summary for a single zone.
    Returned by GET /api/v1/availability/{zone_id}
    """
    zone_id: int
    zone_name: str
    location: str
    total_spaces: int
    available_count: int
    occupied_count: int
    reserved_count: int
    zone_type: str = "PAID"
    hourly_rate: Optional[float] = None
    operating_hours: Optional[str] = None
    rules: Optional[str] = None
    restriction_reason: Optional[str] = None
    spaces: List[SpaceStatusItem]


class ZoneAvailabilitySummary(BaseModel):
    """
    Brief availability summary — no space list.
    Used in GET /api/v1/availability (all zones overview).
    """
    zone_id: int
    zone_name: str
    location: str
    total_spaces: int
    available_count: int
    occupied_count: int
    reserved_count: int
    zone_type: str = "PAID"
    hourly_rate: Optional[float] = None
    operating_hours: Optional[str] = None
    rules: Optional[str] = None
    restriction_reason: Optional[str] = None