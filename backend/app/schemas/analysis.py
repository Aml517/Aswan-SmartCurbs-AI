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


class LiveStreamStartRequest(BaseModel):
    mode: Optional[str] = "windy"  # windy, file, replay, webcam, rtsp
    source: Optional[str] = None
    source_name: Optional[str] = "Windy Live Webcam - Portul Turistic Jurilovca (#1793889300)"
    zone_id: int = 1
    is_external_demo: bool = True
    max_fps: float = 12.0
    warning_threshold: Optional[float] = None


class LiveStreamStatusResponse(BaseModel):
    is_running: bool
    is_connected: bool
    status: str
    source_name: str
    is_external_demo: bool
    zone_id: int
    last_frame_processed_at: Optional[str] = None
    last_error: Optional[str] = None
    frames_processed: int
    frames_received: Optional[int] = 0
    frames_decoded: Optional[int] = 0
    frames_inferred: Optional[int] = 0
    current_fps: float
    vehicles_detected_count: int
    current_detections_count: Optional[int] = 0
    active_track_ids: List[int] = []
    active_tracks_count: Optional[int] = 0
    occupancy_summary: dict = {}
    active_distances: List[dict] = []
    min_distance: Optional[float] = None
    min_distance_str: Optional[str] = "N/A"
    distance_warning_count: int = 0
    candidate_violations_count: int = 0
    is_calibrated: bool = False
    calibration_note: str = ""
    session_id: Optional[int] = None
    session_uuid: Optional[str] = None

