"""Parking occupancy (Word doc 5.1): vehicle -> parking/curb space -> Occupied / Free -> available capacity.

A space is Occupied when a tracked vehicle's reference point falls inside the space polygon
(config.json -> parking_spaces; "occupancy_point": "center" or "ground").
"""
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from common import CFG, path, point_in_polygon, save_json
from track import INPUT_VIDEO, load_tracks, process_video

PARKING_SPACES: dict = {int(k): [tuple(p) for p in v] for k, v in CFG["parking_spaces"].items()}
OCCUPANCY_OUTPUT_VIDEO = path("outputs/parking_occupancy_output.mp4")
OCCUPANCY_JSON = path("outputs/occupancy_results.json")


def _reference_point(vehicle):
    if CFG.get("occupancy_point", "center") == "ground":
        return (vehicle["center_x"], vehicle["bounding_box"][3])
    return (vehicle["center_x"], vehicle["center_y"])


def is_vehicle_in_parking_space(vehicle, parking_polygon) -> bool:
    return point_in_polygon(_reference_point(vehicle), parking_polygon)


def calculate_frame_occupancy(frame_detections, parking_spaces=PARKING_SPACES) -> dict:
    """{space_id: {"status": "Free"|"Occupied", "vehicle_id": id|None, "confidence": float|None}}"""
    occupancy = {sid: {"status": "Free", "vehicle_id": None, "confidence": None} for sid in parking_spaces}
    for sid, polygon in parking_spaces.items():
        inside = [v for v in frame_detections if is_vehicle_in_parking_space(v, polygon)]
        if inside:
            best = max(inside, key=lambda v: float(v["confidence"]))
            occupancy[sid] = {"status": "Occupied", "vehicle_id": int(best["track_id"]),
                              "confidence": round(float(best["confidence"]), 3)}
    return occupancy


def summarize_spaces(spaces: dict) -> dict:
    """Available capacity for one frame."""
    total = len(spaces)
    occupied = sum(1 for s in spaces.values() if s["status"] == "Occupied")
    return {"total": total, "occupied": occupied, "available": total - occupied}


def calculate_all_occupancy(all_detections, parking_spaces=PARKING_SPACES) -> list:
    results = []
    for i, dets in enumerate(all_detections, 1):
        number = dets[0].get("frame_number", i) if dets else i
        spaces = calculate_frame_occupancy(dets, parking_spaces)
        results.append({"frame_number": number, "spaces": spaces, "capacity": summarize_spaces(spaces)})
    return results


def draw_parking_spaces(frame, parking_spaces, occupancy):
    """Green = Free, Red = Occupied."""
    for sid, polygon in parking_spaces.items():
        info = occupancy[sid]
        busy = info["status"] == "Occupied"
        color = (0, 0, 255) if busy else (0, 255, 0)
        pts = np.asarray(polygon, dtype=np.int32)
        cv2.polylines(frame, [pts], True, color, 2)
        label = f"Space {sid}: {info['status']}" + (f" ID {info['vehicle_id']}" if busy else "")
        cv2.putText(frame, label, tuple(int(v) for v in pts[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
    return frame


def process_occupancy_video(all_detections=None, output_path=OCCUPANCY_OUTPUT_VIDEO, save_video=True,
                            json_path=OCCUPANCY_JSON):
    """Full occupancy pipeline. Uses cached tracks when available; writes video + JSON (for API/dashboard)."""
    if all_detections is None:
        all_detections, _ = load_tracks()
        if all_detections is None:
            all_detections = process_video()
    results = calculate_all_occupancy(all_detections)

    if save_video:
        cap = cv2.VideoCapture(str(INPUT_VIDEO))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open input video: {INPUT_VIDEO}")
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), cap.get(cv2.CAP_PROP_FPS) or 25.0, (w, h))
        for r in results:
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(draw_parking_spaces(frame, PARKING_SPACES, r["spaces"]))
        cap.release(); writer.release()

    save_json(results, json_path)
    n = max(len(results), 1)
    print("Occupancy summary:")
    for sid in PARKING_SPACES:
        busy = sum(1 for r in results if r["spaces"][sid]["status"] == "Occupied")
        print(f"  Space {sid}: occupied {100 * busy / n:.0f}% of {n} frames")
    if results:
        c = results[-1]["capacity"]
        print(f"  Last frame: {c['available']} of {c['total']} spaces available")
    print(f"Saved: {json_path}")
    return results


if __name__ == "__main__":
    process_occupancy_video()
