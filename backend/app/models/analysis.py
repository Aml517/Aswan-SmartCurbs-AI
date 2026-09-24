from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class AnalysisJob(Base):
    """
    Tracks an automated AI video analysis execution job on an uploaded or demo video.
    """
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("parking_zones.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    input_video_path = Column(String(500), nullable=False)
    output_video_path = Column(String(500), nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, processing, completed, failed
    
    # Aggregated analysis results
    vehicles_detected_count = Column(Integer, default=0, nullable=False)
    occupied_spaces_count = Column(Integer, default=0, nullable=False)
    available_spaces_count = Column(Integer, default=0, nullable=False)
    min_vehicle_distance_cm = Column(Float, nullable=True)
    avg_vehicle_distance_cm = Column(Float, nullable=True)
    calibration_method = Column(String(100), default="perspective_homography", nullable=False)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    detections = relationship("VehicleDetectionLog", back_populates="job", cascade="all, delete-orphan")


class VehicleDetectionLog(Base):
    """
    Per-vehicle detection log containing tracking identity, parking space mapping,
    bounding box coordinates, and homography-derived centimeter ground distance.
    """
    __tablename__ = "vehicle_detection_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    vehicle_track_id = Column(Integer, nullable=False)
    space_id = Column(Integer, ForeignKey("parking_spaces.id"), nullable=True)
    
    # Bounding box & pixel coordinates
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    center_x = Column(Float, nullable=False)
    center_y = Column(Float, nullable=False)
    
    # Calibrated ground-plane measurements in centimeters
    ground_x_cm = Column(Float, nullable=True)
    ground_y_cm = Column(Float, nullable=True)
    nearest_vehicle_id = Column(Integer, nullable=True)
    nearest_distance_cm = Column(Float, nullable=True)
    
    is_occupying_space = Column(Boolean, default=False, nullable=False)
    confidence = Column(Float, default=0.95, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    job = relationship("AnalysisJob", back_populates="detections")
