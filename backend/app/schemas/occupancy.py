from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class OccupancyUpdate(BaseModel):
    """
    The exact JSON body the AI module must POST to /api/v1/occupancy.
    This is the integration contract between AI and Backend.
    """
    zone_id: int = Field(..., description="ID of the parking zone")
    space_id: int = Field(..., description="ID of the specific parking space")
    status: Literal["occupied", "available"] = Field(..., description="Detected status of the space")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score between 0.0 and 1.0")


class OccupancyResponse(BaseModel):
    """
    What the backend sends back to the AI after processing the update.
    """
    message: str
    space_id: int
    new_status: str
    confidence: float
    logged_at: datetime

    class Config:
        from_attributes = True