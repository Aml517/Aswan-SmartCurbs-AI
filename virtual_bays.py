"""Virtual parking bays (Word doc 5.3): estimate curb bays from camera observations instead of painted lines.

Pipeline: tracked vehicles -> keep the ones parked (stationary) -> observed bays -> free gaps that could
fit another vehicle -> virtual bays -> occupancy. The estimate is made in image space (no calibration needed).
"""
from collections import defaultdict

import numpy as np

from common import CFG, iou


def group_tracks(all_detections):
    tracks = defaultdict(list)
    for frame in all_detections:
        for d in frame:
            tracks[d["track_id"]].append(d)
    return tracks


def trailing_stationary(detections, tolerance_px):
    """Longest run at the END of a track where the vehicle did not move more than tolerance_px."""
    if not detections:
        return []
    centers = np.array([[d["center_x"], d["center_y"]] for d in detections])
    anchor = np.median(centers[-min(len(centers), 5):], axis=0)
    start = len(centers) - 1
    while start > 0 and np.linalg.norm(centers[start - 1] - anchor) <= tolerance_px:
        start -= 1
    return detections[start:]


def parked_runs(all_detections, fps, cfg=CFG):
    """{track_id: stationary run} for vehicles parked at least `stationary_seconds`."""
    t = cfg["thresholds"]
    min_frames = max(2, int(t["stationary_seconds"] * fps))
    runs = {}
    for tid, ds in group_tracks(all_detections).items():
        run = trailing_stationary(ds, t["stationary_px"] * 3)
        if len(run) >= min_frames:
            runs[tid] = run
    return runs


def estimate_virtual_bays(all_detections, fps, cfg=CFG):
    boxes = []
    for run in parked_runs(all_detections, fps, cfg).values():
        boxes.append(np.median(np.array([d["bounding_box"] for d in run]), axis=0).astype(int).tolist())
    merged = []
    for b in sorted(boxes, key=lambda b: b[0]):
        if not any(iou(b, m) > 0.5 for m in merged):
            merged.append(b)
    if not merged:
        return {"median_vehicle_width_px": None, "bays": [], "note": "No parked vehicles observed yet."}
    width = float(np.median([b[2] - b[0] for b in merged]))
    bays = [{"id": i + 1, "bbox": b, "source": "observed"} for i, b in enumerate(merged)]
    free = []
    for left, right in zip(merged, merged[1:]):
        vertical = min(left[3], right[3]) - max(left[1], right[1])
        gap = right[0] - left[2]
        if vertical < 0.5 * min(left[3] - left[1], right[3] - right[1]) or gap < 0.8 * width:
            continue
        n = int(gap // width)
        start = left[2] + (gap - n * width) / 2
        for k in range(n):
            free.append({"id": len(bays) + len(free) + 1, "source": "estimated_free",
                         "bbox": [int(start + k * width), left[1], int(start + (k + 1) * width), left[3]]})
    return {"median_vehicle_width_px": round(width, 1), "bays": bays + free,
            "note": "Image-space estimate; 'observed' = a vehicle is parked there, 'estimated_free' = a gap wide enough for one more."}


def virtual_bay_occupancy(bays, frame_detections):
    """{bay_id: 'Occupied'|'Free'} for one frame."""
    out = {}
    for bay in bays:
        x1, y1, x2, y2 = bay["bbox"]
        busy = any(x1 <= d["center_x"] <= x2 and y1 <= d["center_y"] <= y2 for d in frame_detections)
        out[bay["id"]] = "Occupied" if busy else "Free"
    return out
