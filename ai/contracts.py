"""Agreed data contracts between the AI modules and the backend.

Member 3 (Detection & Tracking) -> Member 4 (Virtual Bays & Occupancy) -> Member 5 (Backend).

* frame_id is 0-based (same as OpenCV and ground_truth.json); timestamp = frame_id / fps (seconds).
* tracks.json keeps the internal names (frame_number is 1-based, class_name, bounding_box); this module
  converts them to the agreed names so no other file has to change.
"""
from typing import Any, Dict, List, Optional

STATUS_OCCUPIED = "occupied"
STATUS_AVAILABLE = "available"
VALID_STATUSES = (STATUS_OCCUPIED, STATUS_AVAILABLE)


def frame_message(frame_id: int, detections: List[Dict[str, Any]], fps: float) -> Dict[str, Any]:
    """One frame in the Detection -> Occupancy format."""
    fps = float(fps) if fps else 25.0
    return {
        "frame_id": int(frame_id),
        "timestamp": round(frame_id / fps, 3),
        "vehicles": [
            {
                "track_id": int(d["track_id"]),
                "class": d["class_name"],
                "confidence": round(float(d["confidence"]), 4),
                "bbox": [int(v) for v in d["bounding_box"]],
            }
            for d in detections
        ],
    }


def frames_from_tracks(all_detections: List[List[Dict[str, Any]]], fps: float) -> List[Dict[str, Any]]:
    """Convert the whole tracks.json 'frames' list (index = frame_id)."""
    return [frame_message(i, dets, fps) for i, dets in enumerate(all_detections)]


def zone_payload(zone_id: int, spaces: Dict[Any, Dict[str, Any]], space_map: Dict[str, int]) -> Dict[str, Any]:
    """One frame of occupancy in the Occupancy -> Backend format.

    `spaces` is calculate_frame_occupancy() output ({ai_space_id: {status, vehicle_id, confidence}}).
    `space_map` maps AI space ids to backend space ids (config.json -> backend.space_map).
    AI spaces without a mapping cannot be sent to the backend, so they are left out.
    """
    items = []
    for ai_id, info in spaces.items():
        backend_id = space_map.get(str(ai_id))
        if backend_id is None:
            continue
        busy = info["status"] == "Occupied"
        items.append({
            "space_id": int(backend_id),
            "status": STATUS_OCCUPIED if busy else STATUS_AVAILABLE,
            "track_id": info.get("vehicle_id") if busy else None,
            "confidence": info.get("confidence") if busy else None,   # optional extra field
        })
    items.sort(key=lambda i: i["space_id"])
    occupied = sum(1 for i in items if i["status"] == STATUS_OCCUPIED)
    total = len(items)
    return {
        "zone_id": int(zone_id),
        "occupancy": items,
        "occupied_count": occupied,
        "available_count": total - occupied,
        "occupancy_percentage": round(100 * occupied / total) if total else 0,
    }


def validate_zone_payload(payload: Dict[str, Any]) -> List[str]:
    """Return a list of problems (empty list = valid). Each space must appear once with one valid status."""
    errors: List[str] = []
    items = payload.get("occupancy")
    if not isinstance(payload.get("zone_id"), int):
        errors.append("zone_id must be an integer")
    if not isinstance(items, list):
        return errors + ["occupancy must be a list"]
    seen = set()
    for it in items:
        sid = it.get("space_id")
        if sid in seen:
            errors.append(f"space_id {sid} appears more than once")
        seen.add(sid)
        if it.get("status") not in VALID_STATUSES:
            errors.append(f"space_id {sid}: invalid status {it.get('status')!r}")
        if it.get("status") == STATUS_AVAILABLE and it.get("track_id") is not None:
            errors.append(f"space_id {sid}: available space must have track_id null")
        if it.get("status") == STATUS_OCCUPIED and it.get("track_id") is None:
            errors.append(f"space_id {sid}: occupied space needs a track_id")
    occ = sum(1 for it in items if it.get("status") == STATUS_OCCUPIED)
    if payload.get("occupied_count") != occ:
        errors.append("occupied_count does not match the spaces")
    if payload.get("available_count") != len(items) - occ:
        errors.append("available_count does not match the spaces")
    expected_pct = round(100 * occ / len(items)) if items else 0
    if payload.get("occupancy_percentage") != expected_pct:
        errors.append("occupancy_percentage does not match the spaces")
    return errors
