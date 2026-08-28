from pydantic import BaseModel
from typing import List


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