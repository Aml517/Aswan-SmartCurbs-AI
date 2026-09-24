from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ─── Zone Schemas ────────────────────────────────────────────

class ZoneCreate(BaseModel):
    """Used when creating a new parking zone (POST /api/v1/zones)."""
    name: str
    location: str
    total_spaces: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone_type: Optional[str] = "PAID"
    hourly_rate: Optional[float] = None
    operating_hours: Optional[str] = None
    rules: Optional[str] = None
    restriction_reason: Optional[str] = None


class ZoneResponse(BaseModel):
    """Returned when reading zone data."""
    id: int
    name: str
    location: str
    total_spaces: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone_type: str = "PAID"
    hourly_rate: Optional[float] = None
    operating_hours: Optional[str] = None
    rules: Optional[str] = None
    restriction_reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Space Schemas ────────────────────────────────────────────

class SpaceCreate(BaseModel):
    """Used when adding a parking space to a zone."""
    zone_id: int
    space_number: str


class SpaceResponse(BaseModel):
    """Returned when reading space data."""
    id: int
    zone_id: int
    space_number: str
    status: str
    last_updated: datetime

    class Config:
        from_attributes = True