from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class VehicleDetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    frame_number: int
    vehicle_track_id: int
    space_id: Optional[int] = None
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    center_x: float
    center_y: float
    ground_x_cm: Optional[float] = None
    ground_y_cm: Optional[float] = None
    nearest_vehicle_id: Optional[int] = None
    nearest_distance_cm: Optional[float] = None
    is_occupying_space: bool
    confidence: float
    created_at: datetime


class AnalysisJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    zone_id: int
    filename: str
    status: str
    vehicles_detected_count: int
    occupied_spaces_count: int
    available_spaces_count: int
    min_vehicle_distance_cm: Optional[float] = None
    avg_vehicle_distance_cm: Optional[float] = None
    calibration_method: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    output_video_url: Optional[str] = None


class AnalysisJobDetailResponse(AnalysisJobResponse):
    recent_detections: List[VehicleDetectionResponse] = []
