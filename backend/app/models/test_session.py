from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


class AITestSession(Base):
    """
    Persisted test session summary tracking quantitative metrics across all 8 pipeline stages.
    Completely isolated from operational parking occupancy and reservation records.
    """
    __tablename__ = "ai_test_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_uuid = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_mode = Column(String(50), nullable=False)
    source_name = Column(String(255), nullable=False)
    is_external_demo = Column(Boolean, default=True, nullable=False)
    is_calibrated = Column(Boolean, default=False, nullable=False)
    calibration_method = Column(String(100), default="uncalibrated_pixel_space", nullable=False)
    
    # Runtime & Ingestion Telemetry
    total_frames = Column(Integer, default=0, nullable=False)
    elapsed_seconds = Column(Float, default=0.0, nullable=False)
    average_fps = Column(Float, default=0.0, nullable=False)
    dropped_frames = Column(Integer, default=0, nullable=False)
    reconnect_count = Column(Integer, default=0, nullable=False)
    avg_latency_ms = Column(Float, default=0.0, nullable=False)
    
    # Detection & Tracking Accuracy
    detection_precision = Column(Float, nullable=True)
    detection_recall = Column(Float, nullable=True)
    detection_f1 = Column(Float, nullable=True)
    mean_iou = Column(Float, nullable=True)
    tracking_id_switches = Column(Integer, default=0, nullable=False)
    tracking_fragmentations = Column(Integer, default=0, nullable=False)
    
    # Distance Measurement & Evaluation
    distance_pairs_measured = Column(Integer, default=0, nullable=False)
    distance_unit = Column(String(50), default="px (uncalibrated)", nullable=False)
    distance_mae = Column(Float, nullable=True)
    distance_rmse = Column(Float, nullable=True)
    distance_tolerance_rate = Column(Float, nullable=True)
    
    # JSON blobs for stage-by-stage status & raw metrics
    stage_status_json = Column(Text, nullable=True)  # JSON { "stage_a": "PASS", ... }
    summary_notes = Column(Text, nullable=True)

    # Relationships
    measurements = relationship("DistanceMeasurementRecord", back_populates="session", cascade="all, delete-orphan")


class DistanceMeasurementRecord(Base):
    """
    Individual vehicle-to-vehicle distance measurement record captured during test execution.
    """
    __tablename__ = "distance_measurement_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("ai_test_sessions.id"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    vehicle_1_id = Column(Integer, nullable=False)
    vehicle_2_id = Column(Integer, nullable=False)
    distance = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    calibration_status = Column(String(50), nullable=False)  # calibrated / uncalibrated
    warning_status = Column(String(50), nullable=False)      # normal / warning / critical
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    session = relationship("AITestSession", back_populates="measurements")
