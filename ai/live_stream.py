"""Live video stream processor for Aswan SmartCurbs AI.

Connects to live camera sources (RTSP, HLS, Windy Webcams, or local cameras)
and runs continuous real-time YOLOv8 vehicle detection, ByteTrack tracking,
space occupancy mapping, and candidate violation monitoring in a background thread.
"""
import logging
import os
import sys
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Ensure the ai directory is on sys.path for internal imports
AI_DIR = Path(__file__).resolve().parent
if str(AI_DIR) not in sys.path:
    sys.path.insert(0, str(AI_DIR))

import cv2
import numpy as np

try:
    from capture import VideoSource
    from common import CFG, get_homography, path
    from distance import calculate_frame_distances, compute_relevant_pairwise_distances, describe, ground_contact_point
    from occupancy import PARKING_SPACES, calculate_frame_occupancy, summarize_spaces
    from track import MODEL_NAME, TRACKER_CONFIG, VEHICLE_CLASSES
except ImportError:
    from ai.capture import VideoSource
    from ai.common import CFG, get_homography, path
    from ai.distance import calculate_frame_distances, compute_relevant_pairwise_distances, describe, ground_contact_point
    from ai.occupancy import PARKING_SPACES, calculate_frame_occupancy, summarize_spaces
    from ai.track import MODEL_NAME, TRACKER_CONFIG, VEHICLE_CLASSES

logger = logging.getLogger(__name__)


class LiveStreamProcessor:
    """Thread-safe background live stream analyzer with lifecycle control."""

    _instance_lock = threading.Lock()

    def __init__(
        self,
        mode: Optional[str] = None,
        source: Optional[str] = None,
        source_name: Optional[str] = None,
        is_external_demo: bool = True,
        zone_id: int = 1,
        max_fps: float = 12.0,
        warning_threshold: Optional[float] = None,
        on_status_update: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.mode = mode or os.getenv("LIVE_STREAM_MODE") or "windy"
        self.source = source or os.getenv("LIVE_STREAM_URL")
        self.source_name = source_name or "Windy Live Webcam - Portul Turistic Jurilovca (#1793889300)"
        self.is_external_demo = is_external_demo
        self.zone_id = zone_id
        self.max_fps = max_fps
        self.warning_threshold = warning_threshold
        self.on_status_update = on_status_update

        # Threading & lifecycle control
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._frame_lock = threading.Lock()

        # Shared state & metrics
        self.is_running = False
        self.is_connected = False
        self.status = "stopped"  # stopped, connecting, running, reconnecting, error
        self.last_frame_processed_at: Optional[str] = None
        self.last_error: Optional[str] = None
        self.frames_processed = 0
        self.frames_received = 0
        self.frames_decoded = 0
        self.frames_inferred = 0
        self.current_fps = 0.0
        self.vehicles_detected_count = 0
        self.active_track_ids: List[int] = []
        self.occupancy_summary = {"total": len(PARKING_SPACES), "occupied": 0, "available": len(PARKING_SPACES)}
        self.active_distances: List[Dict[str, Any]] = []
        self._latest_annotated_jpeg: Optional[bytes] = None
        self.candidate_violations_count = 0
        self.is_calibrated = False if self.is_external_demo else (get_homography() is not None)
        self.calibration_note = (
            "External webcam perspective; metric ground calibration uncalibrated."
            if self.is_external_demo
            else "Zone homography calibration applied."
        )

        # Cached Model (loaded once)
        self._model = None

    def get_latest_frame_jpeg(self) -> Optional[bytes]:
        """Returns the most recent annotated JPEG frame bytes for browser streaming."""
        with self._frame_lock:
            return self._latest_annotated_jpeg

    def start(self) -> bool:
        """Starts the live stream processing thread idempotently."""
        with self._instance_lock:
            if self.is_running and self._thread is not None and self._thread.is_alive():
                logger.info("LiveStreamProcessor is already running (duplicate start ignored).")
                return True

            self._stop_event.clear()
            self.is_running = True
            self.status = "connecting"
            self.last_error = None

            # Pre-warm model in calling thread if not loaded yet
            try:
                self._get_model()
            except Exception as e:
                logger.warning("Model pre-warming note: %s", e)

            self._thread = threading.Thread(
                target=self._run_loop,
                name="LiveStreamProcessorThread",
                daemon=True,
            )
            self._thread.start()
            logger.info("Live stream processing started for '%s' in background thread.", self.source_name)
            return True

    def stop(self) -> bool:
        """Stops the live stream processing thread cleanly and releases capture."""
        with self._instance_lock:
            if not self.is_running:
                return True

            logger.info("Stopping live stream processing for '%s'...", self.source_name)
            self._stop_event.set()
            self.is_running = False
            self.status = "stopped"
            self.is_connected = False

            if self._thread is not None and self._thread.is_alive():
                self._thread.join(timeout=3.0)
            self._thread = None
            logger.info("Live stream processing stopped successfully.")
            return True

    def get_status(self) -> Dict[str, Any]:
        """Returns sanitized status dictionary suitable for API responses without exposing secret credentials."""
        with self._lock:
            min_dist = min([d["distance"] for d in self.active_distances]) if self.active_distances else None
            min_dist_str = f"{min_dist:.1f} {self.active_distances[0]['unit']}" if min_dist is not None and self.active_distances else "N/A"
            warning_cnt = sum(1 for d in self.active_distances if d.get("warning_status") in ("warning", "critical"))
            return {
                "is_running": self.is_running,
                "is_connected": self.is_connected,
                "status": self.status,
                "source_name": self.source_name,
                "is_external_demo": self.is_external_demo,
                "zone_id": self.zone_id,
                "last_frame_processed_at": self.last_frame_processed_at,
                "last_error": self.last_error,
                "frames_processed": self.frames_processed,
                "frames_received": self.frames_received,
                "frames_decoded": self.frames_decoded,
                "frames_inferred": self.frames_inferred,
                "current_fps": round(self.current_fps, 1),
                "vehicles_detected_count": self.vehicles_detected_count,
                "current_detections_count": self.vehicles_detected_count,
                "active_track_ids": list(self.active_track_ids),
                "active_tracks_count": len(self.active_track_ids),
                "occupancy_summary": dict(self.occupancy_summary),
                "active_distances": list(self.active_distances),
                "min_distance": min_dist,
                "min_distance_str": min_dist_str,
                "distance_warning_count": warning_cnt,
                "candidate_violations_count": self.candidate_violations_count,
                "is_calibrated": self.is_calibrated,
                "calibration_note": self.calibration_note,
            }

    def _get_model(self):
        """Loads and caches the YOLO model singleton."""
        if self._model is None:
            from ultralytics import YOLO
            model_path = path(MODEL_NAME) if path(MODEL_NAME).exists() else MODEL_NAME
            self._model = YOLO(str(model_path))
        return self._model

    def _run_loop(self):
        """Main background frame ingestion and computer vision processing loop."""
        src: Optional[VideoSource] = None
        rolling_times = deque(maxlen=20)
        class_ids = None

        try:
            # 1. Initialize Video Source
            src = VideoSource(mode=self.mode, source=self.source, target_fps=self.max_fps)
            src.open()
            self.is_connected = True
            self.status = "running"
            logger.info("Live camera capture opened (%dx%d @ %.1f FPS).", src.width, src.height, src.fps)

            # 2. Prepare YOLO Model
            model = self._get_model()
            class_ids = [i for i, n in model.names.items() if n in VEHICLE_CLASSES]
            conf_thresh = CFG.get("confidence", 0.35)
            H = get_homography() if not self.is_external_demo else None

            # Frame pacing interval (e.g. 1 / 12s = ~83ms between frames)
            min_frame_interval = 1.0 / self.max_fps if self.max_fps > 0 else 0.05
            last_process_time = 0.0

            while not self._stop_event.is_set():
                now = time.time()
                if now - last_process_time < min_frame_interval:
                    time.sleep(0.01)
                    continue

                self.frames_received += 1
                ok, frame, loop_flag = src.read_frame()
                if not ok:
                    if self._stop_event.is_set():
                        break
                    with self._lock:
                        self.is_connected = src.is_connected
                        self.status = src.status
                    time.sleep(0.5)
                    continue

                self.frames_decoded += 1
                last_process_time = time.time()
                rolling_times.append(last_process_time)
                fps_calc = (len(rolling_times) - 1) / (rolling_times[-1] - rolling_times[0]) if len(rolling_times) > 1 else src.fps

                self.frames_inferred += 1
                # YOLO + ByteTrack Tracking
                res = model.track(
                    frame,
                    persist=True,
                    tracker=TRACKER_CONFIG,
                    classes=class_ids,
                    conf=conf_thresh,
                    verbose=False,
                )[0]

                dets = []
                track_ids = []
                if res.boxes is not None and res.boxes.id is not None:
                    ids = res.boxes.id.int().cpu().tolist()
                    for box, tid in zip(res.boxes, ids):
                        x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
                        name = model.names[int(box.cls[0])]
                        track_ids.append(int(tid))
                        dets.append({
                            "frame_number": src.frame_index,
                            "track_id": int(tid),
                            "class_name": name,
                            "confidence": float(box.conf[0]),
                            "bounding_box": [x1, y1, x2, y2],
                            "center_x": (x1 + x2) / 2,
                            "center_y": (y1 + y2) / 2,
                        })

                # Pairwise Vehicle Distance Measurement
                distances = compute_relevant_pairwise_distances(
                    dets,
                    H=H,
                    max_pairs=6,
                    warning_threshold=self.warning_threshold,
                )

                # Space Occupancy Evaluation
                if not self.is_external_demo and PARKING_SPACES:
                    frame_occ = calculate_frame_occupancy(dets, PARKING_SPACES)
                    cap_summary = summarize_spaces(frame_occ)
                else:
                    # For external demo camera without calibrated Aswan bays, report external metrics
                    cap_summary = {"total": len(PARKING_SPACES), "occupied": 0, "available": len(PARKING_SPACES)}

                # Render Visible Annotations on Live Frame
                ann_frame = frame.copy()

                # 1. Draw vehicle bounding boxes, labels, and bottom-center ground contact points
                for d in dets:
                    bx1, by1, bx2, by2 = d["bounding_box"]
                    tid = d["track_id"]
                    cls_name = d["class_name"]
                    conf = d["confidence"]

                    # Bounding Box (Teal/Emerald)
                    cv2.rectangle(ann_frame, (bx1, by1), (bx2, by2), (0, 200, 120), 2)

                    # Header Badge: [ID: X | car 0.85]
                    badge_text = f"ID:{tid} | {cls_name} {conf:.2f}"
                    (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                    cv2.rectangle(ann_frame, (bx1, max(0, by1 - 20)), (bx1 + tw + 8, by1), (3, 22, 53), -1)
                    cv2.putText(ann_frame, badge_text, (bx1 + 4, max(14, by1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

                    # Ground Contact Point (Yellow Dot at bottom-center)
                    gpt = ground_contact_point(d)
                    cv2.circle(ann_frame, (int(gpt[0]), int(gpt[1])), 5, (0, 255, 255), -1)
                    cv2.circle(ann_frame, (int(gpt[0]), int(gpt[1])), 7, (0, 180, 200), 1)

                # 2. Draw connecting lines and distance pills between vehicle pairs
                for p in distances:
                    pt_a = (int(p["point_a"][0]), int(p["point_a"][1]))
                    pt_b = (int(p["point_b"][0]), int(p["point_b"][1]))

                    if p["warning_status"] == "critical":
                        color = (0, 0, 255)      # Red
                        pill_bg = (0, 0, 180)
                    elif p["warning_status"] == "warning":
                        color = (0, 165, 255)    # Amber
                        pill_bg = (0, 120, 200)
                    else:
                        color = (255, 200, 0)    # Cyan
                        pill_bg = (30, 41, 59)

                    # Connecting Line
                    cv2.line(ann_frame, pt_a, pt_b, color, 2, cv2.LINE_AA)

                    # Midpoint Distance Pill
                    mid = (int(p["midpoint"][0]), int(p["midpoint"][1]))
                    dist_label = f"ID {p['vehicle_1_id']} <-> ID {p['vehicle_2_id']}: {p['distance']:.0f} {p['unit']}"
                    (ltw, lth), _ = cv2.getTextSize(dist_label, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
                    cv2.rectangle(ann_frame, (mid[0] - ltw // 2 - 4, mid[1] - lth - 6), (mid[0] + ltw // 2 + 4, mid[1] + 4), pill_bg, -1)
                    cv2.rectangle(ann_frame, (mid[0] - ltw // 2 - 4, mid[1] - lth - 6), (mid[0] + ltw // 2 + 4, mid[1] + 4), color, 1)
                    cv2.putText(ann_frame, dist_label, (mid[0] - ltw // 2, mid[1] - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

                # 3. Top Info Banner HUD
                overlay = ann_frame.copy()
                cv2.rectangle(overlay, (0, 0), (ann_frame.shape[1], 40), (15, 23, 42), -1)
                cv2.addWeighted(overlay, 0.75, ann_frame, 0.25, 0, ann_frame)
                calib_str = "CALIBRATED (cm)" if self.is_calibrated else "UNCALIBRATED (px)"
                dist_str = f"Distances: {len(distances)}" if len(distances) > 0 else "Distances: 0 (N/A)"
                hud_text = (
                    f"NilePulse ITS Live AI | FPS: {fps_calc:.1f} | Vehicles: {len(dets)} | "
                    f"{dist_str} | Calib: {calib_str}"
                )
                cv2.putText(ann_frame, hud_text, (16, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 1, cv2.LINE_AA)

                # 4. Cache JPEG encoded bytes for browser streaming
                ok_enc, buf = cv2.imencode(".jpg", ann_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ok_enc:
                    with self._frame_lock:
                        self._latest_annotated_jpeg = buf.tobytes()

                # Update live state
                with self._lock:
                    self.is_connected = True
                    self.status = "running"
                    self.frames_processed += 1
                    self.current_fps = fps_calc
                    self.vehicles_detected_count = len(dets)
                    self.active_track_ids = track_ids
                    self.occupancy_summary = cap_summary
                    self.active_distances = distances
                    self.last_frame_processed_at = datetime.now(timezone.utc).isoformat()
                    self.last_error = None

                # Invoke status callback if provided (e.g. database persistence hook)
                if self.on_status_update is not None and self.frames_processed % 10 == 0:
                    try:
                        self.on_status_update(self.get_status())
                    except Exception as e:
                        logger.warning("Error in on_status_update callback: %s", e)

        except Exception as e:
            logger.error("LiveStreamProcessor loop error: %s", e, exc_info=True)
            with self._lock:
                self.status = "error"
                self.is_connected = False
                self.last_error = str(e)
        finally:
            if src is not None:
                src.release()
            with self._lock:
                self.is_running = False
                self.is_connected = False
                if self.status != "error":
                    self.status = "stopped"
            logger.info("LiveStreamProcessor loop terminated cleanly.")
