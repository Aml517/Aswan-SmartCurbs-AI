import os
import math
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.models.analysis import AnalysisJob, VehicleDetectionLog
from app.models.space import ParkingSpace
from app.models.zone import ParkingZone
from app.models.occupancy import OccupancyLog

logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR.parent / "ai" / "yolo11n.pt"
if not MODEL_PATH.exists():
    # Fallback to local model path if inside backend
    MODEL_PATH = BASE_DIR / "ai" / "yolo11n.pt"
if not MODEL_PATH.exists():
    MODEL_PATH = Path("yolo11n.pt")


class CameraCalibrator:
    """
    Computes perspective homography matrix to project 2D image pixels
    to metric ground-plane coordinates in centimeters (cm).
    
    Standard curb parking bay dimension: 250 cm (width) x 500 cm (length).
    """
    def __init__(self, ref_image_points: Optional[np.ndarray] = None, ref_real_cm: Optional[np.ndarray] = None):
        if ref_image_points is None:
            # Default reference polygon corners from standard calibration frame
            self.ref_image_points = np.array([
                [171.0, 242.0],  # Front-Left
                [254.0, 218.0],  # Front-Right
                [263.0, 184.0],  # Back-Right
                [144.0, 145.0]   # Back-Left
            ], dtype=np.float32)
        else:
            self.ref_image_points = np.array(ref_image_points, dtype=np.float32)

        if ref_real_cm is None:
            # Metric ground plane: 250 cm width x 500 cm length
            self.ref_real_cm = np.array([
                [0.0, 0.0],
                [250.0, 0.0],
                [250.0, 500.0],
                [0.0, 500.0]
            ], dtype=np.float32)
        else:
            self.ref_real_cm = np.array(ref_real_cm, dtype=np.float32)

        try:
            self.homography_matrix = cv2.getPerspectiveTransform(self.ref_image_points, self.ref_real_cm)
            self.inv_homography_matrix = cv2.getPerspectiveTransform(self.ref_real_cm, self.ref_image_points)
        except Exception as e:
            logger.warning(f"Homography computation warning: {e}. Using fallback linear scale.")
            self.homography_matrix = None
            self.inv_homography_matrix = None

    def pixel_to_ground_cm(self, px: float, py: float) -> Tuple[float, float]:
        """Maps an image pixel (e.g. bottom-center contact point) to ground (X_cm, Y_cm)."""
        if self.homography_matrix is not None:
            pt = np.array([[[px, py]]], dtype=np.float32)
            transformed = cv2.perspectiveTransform(pt, self.homography_matrix)
            gx, gy = transformed[0][0]
            return round(float(gx), 2), round(float(gy), 2)
        else:
            # Fallback linear scale: ~3.2 cm per pixel
            scale_cm_per_px = 3.2
            return round(px * scale_cm_per_px, 2), round(py * scale_cm_per_px, 2)

    def calculate_distance_cm(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculates Euclidean distance in centimeters between two ground-plane points."""
        gx1, gy1 = self.pixel_to_ground_cm(p1[0], p1[1])
        gx2, gy2 = self.pixel_to_ground_cm(p2[0], p2[1])
        dist_cm = math.sqrt((gx2 - gx1) ** 2 + (gy2 - gy1) ** 2)
        return round(dist_cm, 2)


def is_point_inside_polygon(point: Tuple[int, int], polygon: np.ndarray) -> bool:
    """Check if point is inside polygon."""
    return cv2.pointPolygonTest(polygon, point, False) >= 0


def load_zone_parking_polygons(zone_id: int, db: Session) -> List[Dict[str, Any]]:
    """Loads parking spaces for the zone and prepares convex hull polygons."""
    spaces = db.query(ParkingSpace).filter(ParkingSpace.zone_id == zone_id).all()
    
    # Load default geometry file if available
    json_path = BASE_DIR.parent / "ai" / "parking_spaces.json"
    geo_map = {}
    if json_path.exists():
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
                for item in data:
                    geo_map[item["id"]] = item["points"]
        except Exception:
            pass

    results = []
    for idx, sp in enumerate(spaces):
        # Use geometry from JSON if mapped, else generate synthetic rectangular bay
        if sp.id in geo_map:
            pts = geo_map[sp.id]
        elif (idx + 1) in geo_map:
            pts = geo_map[idx + 1]
        else:
            # Synthesize parking bay polygon for spaces without manual polygon annotation
            base_x = 100 + (idx * 90)
            base_y = 200
            pts = [[base_x, base_y], [base_x + 70, base_y], [base_x + 80, base_y - 80], [base_x + 10, base_y - 80]]

        pts_arr = np.array(pts, dtype=np.int32)
        polygon = cv2.convexHull(pts_arr)
        results.append({
            "space_id": sp.id,
            "space_number": sp.space_number,
            "points": pts,
            "polygon": polygon
        })

    return results


def process_video_analysis(job_id: int, db: Session) -> AnalysisJob:
    """
    Executes full computer vision pipeline on the uploaded video:
    - Object detection & multi-vehicle tracking with YOLO + ByteTrack
    - Homography perspective transformation for real-world centimeter distances
    - Parking space occupancy polygon evaluation
    - Annotated video encoding
    - Structured metrics & database persistence
    """
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        raise ValueError(f"AnalysisJob #{job_id} not found.")

    job.status = "processing"
    db.commit()

    try:
        from ultralytics import YOLO

        input_path = job.input_video_path
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video file not found: {input_path}")

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {input_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        output_dir = Path(job.input_video_path).parent.parent / "processed_videos"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"processed_job_{job.id}.mp4"
        output_path = str(output_dir / output_filename)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        calibrator = CameraCalibrator()
        parking_bays = load_zone_parking_polygons(job.zone_id, db)
        
        # Load YOLO Model
        model = YOLO(str(MODEL_PATH) if MODEL_PATH.exists() else "yolo11n.pt")

        frame_idx = 0
        all_tracked_vehicle_ids = set()
        all_distance_measurements_cm = []
        space_occupancy_states = {b["space_id"]: False for b in parking_bays}
        detection_records_to_insert = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            # Run detection + tracking (Classes: 2=Car, 3=Motorcycle, 5=Bus, 7=Truck)
            results = model.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False,
                classes=[2, 3, 5, 7]
            )

            vehicles_in_frame = []

            if results[0].boxes is not None and results[0].boxes.id is not None:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                ids = results[0].boxes.id.cpu().numpy().astype(int)
                confs = results[0].boxes.conf.cpu().numpy()

                for box, vid, conf in zip(boxes, ids, confs):
                    x1, y1, x2, y2 = box
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    # Bottom-center contact point on ground plane
                    contact_x = int(cx)
                    contact_y = int(y2)
                    
                    gx_cm, gy_cm = calibrator.pixel_to_ground_cm(contact_x, contact_y)
                    all_tracked_vehicle_ids.add(vid)

                    vehicles_in_frame.append({
                        "vehicle_id": int(vid),
                        "bbox": (float(x1), float(y1), float(x2), float(y2)),
                        "center": (cx, cy),
                        "contact": (contact_x, contact_y),
                        "ground_cm": (gx_cm, gy_cm),
                        "confidence": float(conf)
                    })

                    # Draw Bounding Box & Vehicle Tag
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 140, 0), 2)
                    cv2.putText(
                        frame,
                        f"ID:{vid} ({gx_cm:.0f},{gy_cm:.0f}cm)",
                        (int(x1), max(20, int(y1) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (255, 140, 0),
                        2
                    )
                    cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

            # Pairwise Centimeter Distance Calculation between vehicles
            frame_pairwise_dists = []
            for i in range(len(vehicles_in_frame)):
                v1 = vehicles_in_frame[i]
                nearest_vid = None
                min_dist_cm = float("inf")

                for j in range(len(vehicles_in_frame)):
                    if i == j:
                        continue
                    v2 = vehicles_in_frame[j]
                    dist_cm = math.sqrt(
                        (v2["ground_cm"][0] - v1["ground_cm"][0]) ** 2 +
                        (v2["ground_cm"][1] - v1["ground_cm"][1]) ** 2
                    )
                    if dist_cm < min_dist_cm:
                        min_dist_cm = dist_cm
                        nearest_vid = v2["vehicle_id"]

                    # Draw distance line between close vehicles
                    if i < j and dist_cm < 600:  # within 6 meters
                        all_distance_measurements_cm.append(dist_cm)
                        cv2.line(frame, v1["center"], v2["center"], (0, 255, 255), 1)
                        mx = int((v1["center"][0] + v2["center"][0]) / 2)
                        my = int((v1["center"][1] + v2["center"][1]) / 2)
                        cv2.putText(frame, f"{dist_cm:.0f}cm", (mx, my), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 2)

                v1["nearest_vid"] = nearest_vid
                v1["nearest_dist_cm"] = min_dist_cm if nearest_vid is not None else None

            # Evaluate Parking Bays Occupancy
            for bay in parking_bays:
                sp_id = bay["space_id"]
                poly = bay["polygon"]
                is_occupied = False
                occupying_vid = None

                for v in vehicles_in_frame:
                    if is_point_inside_polygon(v["center"], poly) or is_point_inside_polygon(v["contact"], poly):
                        is_occupied = True
                        occupying_vid = v["vehicle_id"]
                        v["assigned_space_id"] = sp_id
                        break

                space_occupancy_states[sp_id] = is_occupied
                color = (0, 0, 255) if is_occupied else (0, 255, 0)
                status_str = f"Occupied (#{occupying_vid})" if is_occupied else "Free"

                # Draw Bay Polygon
                cv2.polylines(frame, [poly], True, color, 2)
                px, py = bay["points"][0]
                cv2.putText(
                    frame,
                    f"{bay['space_number']}: {status_str}",
                    (px, max(20, py - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    2
                )

            # Record sampled detections (every 10 frames to keep DB clean)
            if frame_idx % 10 == 0:
                for v in vehicles_in_frame:
                    detection_records_to_insert.append(VehicleDetectionLog(
                        job_id=job.id,
                        frame_number=frame_idx,
                        vehicle_track_id=v["vehicle_id"],
                        space_id=v.get("assigned_space_id"),
                        bbox_x1=v["bbox"][0],
                        bbox_y1=v["bbox"][1],
                        bbox_x2=v["bbox"][2],
                        bbox_y2=v["bbox"][3],
                        center_x=float(v["center"][0]),
                        center_y=float(v["center"][1]),
                        ground_x_cm=v["ground_cm"][0],
                        ground_y_cm=v["ground_cm"][1],
                        nearest_vehicle_id=v.get("nearest_vid"),
                        nearest_distance_cm=v.get("nearest_dist_cm"),
                        is_occupying_space=(v.get("assigned_space_id") is not None),
                        confidence=v["confidence"]
                    ))

            # Add HUD Overlay
            occupied_count = sum(1 for v in space_occupancy_states.values() if v)
            free_count = len(space_occupancy_states) - occupied_count
            cv2.putText(frame, f"Aswan SmartCurbs AI | Frame {frame_idx}/{total_frames}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Vehicles: {len(vehicles_in_frame)} | Occupied Bays: {occupied_count}/{len(space_occupancy_states)}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            out.write(frame)

        cap.release()
        out.release()

        # Update Database with final results
        job.output_video_path = output_path
        job.status = "completed"
        job.vehicles_detected_count = len(all_tracked_vehicle_ids)
        job.occupied_spaces_count = sum(1 for v in space_occupancy_states.values() if v)
        job.available_spaces_count = len(space_occupancy_states) - job.occupied_spaces_count
        job.min_vehicle_distance_cm = round(min(all_distance_measurements_cm), 1) if all_distance_measurements_cm else None
        job.avg_vehicle_distance_cm = round(sum(all_distance_measurements_cm) / len(all_distance_measurements_cm), 1) if all_distance_measurements_cm else None
        job.completed_at = datetime.now(timezone.utc)

        # Batch insert sample detection logs
        if detection_records_to_insert:
            db.bulk_save_objects(detection_records_to_insert)

        # Update real database parking space records
        for sp_id, is_occ in space_occupancy_states.items():
            sp_obj = db.query(ParkingSpace).filter(ParkingSpace.id == sp_id).first()
            if sp_obj:
                sp_obj.status = "occupied" if is_occ else "available"
                sp_obj.last_updated = datetime.now(timezone.utc)

                # Add Occupancy Log
                db.add(OccupancyLog(
                    zone_id=job.zone_id,
                    space_id=sp_id,
                    status="occupied" if is_occ else "available",
                    confidence=0.95,
                    source=f"ai_job_{job.id}"
                ))

        db.commit()
        db.refresh(job)
        return job

    except Exception as e:
        logger.exception(f"Error during video processing job #{job_id}: {e}")
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        raise e
