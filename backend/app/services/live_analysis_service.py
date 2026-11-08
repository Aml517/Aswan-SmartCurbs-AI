"""Live Video Analysis Coordinator Service for Aswan SmartCurbs AI.

Manages the singleton background LiveStreamProcessor worker thread, prevents
duplicate concurrent workers, and provides thread-safe lifecycle control
(start, stop, status) and telemetry persistence into the database.
"""
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure repository root and ai directory are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AI_DIR = REPO_ROOT / "ai"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(AI_DIR) not in sys.path:
    sys.path.insert(0, str(AI_DIR))

try:
    from ai.live_stream import LiveStreamProcessor
except ImportError:
    from live_stream import LiveStreamProcessor

import json
import time
import uuid

from app.db.database import SessionLocal
from app.models.occupancy import OccupancyLog
from app.models.space import ParkingSpace
from app.models.test_session import AITestSession, DistanceMeasurementRecord

logger = logging.getLogger(__name__)


def _calc_elapsed(ts: Optional[datetime]) -> float:
    if ts is None:
        return 0.0
    now_utc = datetime.now(timezone.utc)
    ts_aware = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
    return max(0.0, (now_utc - ts_aware).total_seconds())


class LiveAnalysisManager:
    """Singleton service controlling the active live camera stream worker."""

    _instance: Optional["LiveAnalysisManager"] = None
    _lock = threading.RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LiveAnalysisManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._processor: Optional[LiveStreamProcessor] = None
        self._processor_lock = threading.RLock()
        self._last_persisted_occupancy: Dict[int, str] = {}
        self.active_session_id: Optional[int] = None
        self.active_session_uuid: Optional[str] = None
        self._last_pair_persisted_time: Dict[tuple, float] = {}
        self._initialized = True

    def start_stream(
        self,
        mode: Optional[str] = None,
        source: Optional[str] = None,
        source_name: Optional[str] = None,
        zone_id: int = 1,
        is_external_demo: bool = True,
        max_fps: float = 12.0,
        warning_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Starts or returns existing live stream processing worker and initializes session tracking."""
        with self._processor_lock:
            if self._processor is not None and self._processor.is_running:
                logger.info("LiveStreamProcessor is already running. Returning active status.")
                st = self.get_status()
                return {
                    "success": True,
                    "message": "Live stream analysis is already active.",
                    "status": st,
                }

            # Initialize a new active database session for distance records
            try:
                with SessionLocal() as db:
                    sess_uuid = str(uuid.uuid4())
                    calib_active = (not is_external_demo)
                    sess = AITestSession(
                        session_uuid=sess_uuid,
                        timestamp=datetime.now(timezone.utc),
                        source_mode=mode or "windy",
                        source_name=source_name or "Windy Live Webcam - Portul Turistic Jurilovca (#1793889300)",
                        is_external_demo=is_external_demo,
                        is_calibrated=calib_active,
                        calibration_method="ground_homography" if calib_active else "uncalibrated_pixel_space",
                        distance_unit="cm" if calib_active else "px (uncalibrated)",
                        stage_status_json=json.dumps({"live_stream": "STREAMING"}),
                        summary_notes="Continuous live surveillance camera stream session.",
                    )
                    db.add(sess)
                    db.commit()
                    db.refresh(sess)
                    self.active_session_id = sess.id
                    self.active_session_uuid = sess.session_uuid
                    self._last_pair_persisted_time.clear()
                    logger.info("Initialized live analysis session #%d (%s)", sess.id, sess_uuid)
            except Exception as e:
                logger.warning("Could not create initial AITestSession: %s", e)

            # Create new processor instance
            self._processor = LiveStreamProcessor(
                mode=mode,
                source=source,
                source_name=source_name,
                is_external_demo=is_external_demo,
                zone_id=zone_id,
                max_fps=max_fps,
                warning_threshold=warning_threshold,
                on_status_update=self._handle_status_update,
            )

            started = self._processor.start()
            if not started:
                return {
                    "success": False,
                    "message": "Failed to start live stream processor worker.",
                    "status": self.get_status(),
                }

            return {
                "success": True,
                "message": "Live stream analysis worker started successfully.",
                "status": self.get_status(),
            }

    def stop_stream(self) -> Dict[str, Any]:
        """Stops the active live stream worker if running."""
        with self._processor_lock:
            if self._processor is None:
                return {
                    "success": True,
                    "message": "No active live stream processor to stop.",
                    "status": {
                        "is_running": False,
                        "is_connected": False,
                        "status": "stopped",
                        "session_id": self.active_session_id,
                        "session_uuid": self.active_session_uuid,
                    },
                }

            self._processor.stop()
            status = self.get_status()

            if self.active_session_id is not None:
                try:
                    with SessionLocal() as db:
                        sess = db.query(AITestSession).filter(AITestSession.id == self.active_session_id).first()
                        if sess:
                            sess.stage_status_json = json.dumps({"live_stream": "STOPPED"})
                            sess.total_frames = status.get("frames_processed", sess.total_frames)
                            sess.average_fps = status.get("current_fps", sess.average_fps)
                            sess.elapsed_seconds = _calc_elapsed(sess.timestamp)
                            db.commit()
                except Exception as e:
                    logger.warning("Error finalizing test session on stop: %s", e)

            return {
                "success": True,
                "message": "Live stream analysis worker stopped successfully.",
                "status": status,
            }

    def get_latest_frame_jpeg(self) -> Optional[bytes]:
        """Retrieves latest annotated JPEG frame bytes from the active worker."""
        with self._processor_lock:
            if self._processor is not None:
                return self._processor.get_latest_frame_jpeg()
            return None

    def get_status(self) -> Dict[str, Any]:
        """Retrieves real-time status of live camera analysis without credentials."""
        with self._processor_lock:
            if self._processor is None:
                return {
                    "is_running": False,
                    "is_connected": False,
                    "status": "stopped",
                    "source_name": "None",
                    "is_external_demo": True,
                    "zone_id": 1,
                    "last_frame_processed_at": None,
                    "last_error": None,
                    "frames_processed": 0,
                    "frames_received": 0,
                    "frames_decoded": 0,
                    "frames_inferred": 0,
                    "current_fps": 0.0,
                    "vehicles_detected_count": 0,
                    "current_detections_count": 0,
                    "active_track_ids": [],
                    "active_tracks_count": 0,
                    "occupancy_summary": {"total": 0, "occupied": 0, "available": 0},
                    "active_distances": [],
                    "min_distance": None,
                    "min_distance_str": "N/A",
                    "distance_warning_count": 0,
                    "candidate_violations_count": 0,
                    "is_calibrated": False,
                    "calibration_note": "No active stream session.",
                    "session_id": self.active_session_id,
                    "session_uuid": self.active_session_uuid,
                }
            st = self._processor.get_status()
            st["session_id"] = self.active_session_id
            st["session_uuid"] = self.active_session_uuid
            return st

    def _handle_status_update(self, status: Dict[str, Any]) -> None:
        """Callback executed every N frames to persist debounced distance measurements and telemetry to DB."""
        if self.active_session_id is not None:
            active_dists = status.get("active_distances", [])
            if active_dists:
                now = time.time()
                to_persist = []
                for p in active_dists:
                    t1, t2 = sorted([int(p.get("vehicle_1_id", 0)), int(p.get("vehicle_2_id", 0))])
                    pair_key = (t1, t2)
                    last_t = self._last_pair_persisted_time.get(pair_key, 0.0)
                    # Deduplicate: persist at most once every 1.5 seconds per vehicle pair
                    if now - last_t >= 1.5:
                        self._last_pair_persisted_time[pair_key] = now
                        to_persist.append(p)

                if to_persist:
                    try:
                        with SessionLocal() as db:
                            for p in to_persist:
                                rec = DistanceMeasurementRecord(
                                    session_id=self.active_session_id,
                                    frame_number=status.get("frames_processed", 1),
                                    vehicle_1_id=p["vehicle_1_id"],
                                    vehicle_2_id=p["vehicle_2_id"],
                                    distance=p["distance"],
                                    unit=p["unit"],
                                    calibration_status=p["calibration_status"],
                                    warning_status=p["warning_status"],
                                )
                                db.add(rec)

                            sess = db.query(AITestSession).filter(AITestSession.id == self.active_session_id).first()
                            if sess:
                                sess.total_frames = status.get("frames_processed", 0)
                                sess.average_fps = status.get("current_fps", 0.0)
                                sess.elapsed_seconds = _calc_elapsed(sess.timestamp)
                                sess.distance_pairs_measured = db.query(DistanceMeasurementRecord).filter(
                                    DistanceMeasurementRecord.session_id == self.active_session_id
                                ).count()
                            db.commit()
                    except Exception as e:
                        logger.warning("Error persisting live distance measurements: %s", e)


# Global singleton instance
live_analysis_manager = LiveAnalysisManager()
