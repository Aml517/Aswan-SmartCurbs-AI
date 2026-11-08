"""Vehicle-to-vehicle distance and curb analysis (Word doc 5.2).

Goal from the supervisor: "Car A - 82 cm - Car B".
  * Calibrated (config.json -> calibration.enabled, made by calibrate.py): the bottom edge of each
    vehicle box is projected onto the ground plane and the gap is measured in centimetres.
  * Not calibrated: only pixel distances are reported. Nothing is ever shown as cm without calibration.
"""
import math
import sys
from pathlib import Path

AI_DIR = Path(__file__).resolve().parent
if str(AI_DIR) not in sys.path:
    sys.path.insert(0, str(AI_DIR))

try:
    from common import CFG, get_homography, point_line_distance, segment_distance, to_ground, save_json, path
    from track import load_tracks, process_video
except ImportError:
    from ai.common import CFG, get_homography, point_line_distance, segment_distance, to_ground, save_json, path
    from ai.track import load_tracks, process_video


def calculate_distance(c1, c2):
    """Euclidean distance between two points, in pixels."""
    return math.hypot(c2[0] - c1[0], c2[1] - c1[1])


def footprint(det):
    """Ground-contact edge of a vehicle: bottom-left and bottom-right of its box."""
    x1, y1, x2, y2 = det["bounding_box"]
    return (x1, y2), (x2, y2)


def gap_cm(det_a, det_b, H):
    """Gap between two vehicles' footprints on the ground plane, in cm (None if not calibrated)."""
    if H is None:
        return None
    a1, a2 = (to_ground(H, p) for p in footprint(det_a))
    b1, b2 = (to_ground(H, p) for p in footprint(det_b))
    return round(segment_distance(a1, a2, b1, b2), 1)


def calculate_frame_distances(frame_detections, H=None):
    out = []
    for i in range(len(frame_detections)):
        for j in range(i + 1, len(frame_detections)):
            a, b = frame_detections[i], frame_detections[j]
            out.append({
                "vehicle_1_id": a["track_id"], "vehicle_2_id": b["track_id"],
                "distance_pixels": round(calculate_distance((a["center_x"], a["center_y"]), (b["center_x"], b["center_y"])), 2),
                "gap_cm": gap_cm(a, b, H),
            })
    return out


def calculate_all_distances(all_detections, H=None):
    """Distances for every frame that has at least two tracked vehicles."""
    H = H if H is not None else get_homography()
    return [{"frame_number": f[0]["frame_number"], "distances": calculate_frame_distances(f, H)}
            for f in all_detections if len(f) >= 2]


def ground_contact_point(det):
    """Returns bottom-center point of vehicle bounding box for ground-plane contact."""
    if "bounding_box" in det:
        x1, y1, x2, y2 = det["bounding_box"]
    elif "box_xyxy" in det:
        x1, y1, x2, y2 = det["box_xyxy"]
    elif "bbox" in det:
        x, y, w, h = det["bbox"]
        x1, y1, x2, y2 = x, y, x + w, y + h
    else:
        raise KeyError("Detection dict must contain 'bounding_box', 'box_xyxy', or 'bbox'")
    return (float((x1 + x2) / 2.0), float(y2))


def calculate_vehicle_pair_distance(det_a, det_b, H=None, warning_threshold=None):
    """
    Computes physical vehicle-to-vehicle distance at ground contact points ((x1+x2)/2, y2).
    - If H is a valid homography: projects points to ground plane (cm) and calculates metric Euclidean distance.
    - If H is None / uncalibrated: reports honest Euclidean pixel distance with calibration_status='uncalibrated'
      and warning_status='uncalibrated' (or 'warning'/'critical' if below proximity threshold).
    Strictly avoids arbitrary multipliers or fabricated values.
    """
    p_a = ground_contact_point(det_a)
    p_b = ground_contact_point(det_b)

    g_a = to_ground(H, p_a) if H is not None else None
    g_b = to_ground(H, p_b) if H is not None else None

    if g_a is not None and g_b is not None:
        # Physical metric distance on calibrated ground plane in centimeters
        dist_val = round(math.hypot(g_b[0] - g_a[0], g_b[1] - g_a[1]), 1)
        unit = "cm"
        cal_status = "calibrated"
        thresh = warning_threshold if warning_threshold is not None else 150.0
        if dist_val <= (thresh / 2.0):
            warning_status = "critical"
            is_warn = True
        elif dist_val <= thresh:
            warning_status = "warning"
            is_warn = True
        else:
            warning_status = "normal"
            is_warn = False
    else:
        # Uncalibrated pixel space distance
        dist_val = round(math.hypot(p_b[0] - p_a[0], p_b[1] - p_a[1]), 1)
        unit = "px (uncalibrated)"
        cal_status = "uncalibrated"
        thresh = warning_threshold if warning_threshold is not None else 80.0
        if dist_val <= (thresh / 2.0):
            warning_status = "critical"
            is_warn = True
        elif dist_val <= thresh:
            warning_status = "warning"
            is_warn = True
        else:
            warning_status = "uncalibrated"
            is_warn = False

    return {
        "vehicle_1_id": det_a.get("track_id", 0),
        "vehicle_2_id": det_b.get("track_id", 0),
        "track_a": det_a.get("track_id", 0),
        "track_b": det_b.get("track_id", 0),
        "point_a": [p_a[0], p_a[1]],
        "point_b": [p_b[0], p_b[1]],
        "ground_point_a": [g_a[0], g_a[1]] if g_a is not None else None,
        "ground_point_b": [g_b[0], g_b[1]] if g_b is not None else None,
        "midpoint": [(p_a[0] + p_b[0]) / 2.0, (p_a[1] + p_b[1]) / 2.0],
        "distance": dist_val,
        "unit": unit,
        "calibration_status": cal_status,
        "warning_status": warning_status,
        "is_warning": is_warn,
        "label": f"Car {det_a.get('track_id', 0)} <-> Car {det_b.get('track_id', 0)}: {dist_val:.0f} {unit}",
    }


def compute_relevant_pairwise_distances(detections, H=None, max_pairs=6, warning_threshold=None):
    """
    Computes pairwise ground distances between relevant vehicle pairs in a frame.
    Limits to nearest pairs to prevent visual clutter and unnecessary O(N^2) overhead.
    """
    if len(detections) < 2:
        return []

    pairs = []
    n = len(detections)
    for i in range(n):
        for j in range(i + 1, n):
            pair_rec = calculate_vehicle_pair_distance(
                detections[i],
                detections[j],
                H=H,
                warning_threshold=warning_threshold,
            )
            pairs.append(pair_rec)

    # Sort pairs by distance ascending (closest vehicles first) and limit to max_pairs
    pairs.sort(key=lambda p: p["distance"])
    return pairs[:max_pairs]


def describe(d):
    """Human-readable label: 'Car 3 - 82 cm - Car 5' (or pixels when uncalibrated)."""
    if d.get("gap_cm") is not None:
        return f"Car {d['vehicle_1_id']} - {d['gap_cm']:.0f} cm - Car {d['vehicle_2_id']}"
    if d.get("distance_pixels") is not None:
        return f"Car {d['vehicle_1_id']} - {d['distance_pixels']:.0f} px (uncalibrated) - Car {d['vehicle_2_id']}"
    if "distance" in d and "unit" in d:
        return f"Car {d['vehicle_1_id']} - {d['distance']:.0f} {d['unit']} - Car {d['vehicle_2_id']}"
    return f"Car {d.get('vehicle_1_id', 0)} - Car {d.get('vehicle_2_id', 0)}"


def curb_distance_cm(det, cfg=CFG, H=None):
    """Distance from a vehicle's ground edge to the curb line in cm (None if curb/calibration missing)."""
    curb, H = cfg.get("curb_line"), H if H is not None else get_homography(cfg)
    if not curb or H is None:
        return None
    a, b = to_ground(H, curb["p1"]), to_ground(H, curb["p2"])
    x1, y1, x2, y2 = det["bounding_box"]
    return round(point_line_distance(to_ground(H, ((x1 + x2) / 2, y2)), a, b), 1)


def nearest_gap_cm(det, frame_detections, H):
    gaps = [g for o in frame_detections if o is not det and (g := gap_cm(det, o, H)) is not None]
    return min(gaps) if gaps else None


def run_distance_analysis(all_detections=None):
    if all_detections is None:
        all_detections, _ = load_tracks()
        if all_detections is None:
            all_detections = process_video()
    results = calculate_all_distances(all_detections)
    save_json(results, path("outputs/distances.json"))
    for r in results[::50][:5]:
        print(f"Frame {r['frame_number']}: " + "; ".join(describe(d) for d in r["distances"][:3]))
    if get_homography() is None:
        print("Note: not calibrated -> pixels only. Run calibrate.py to get centimetres.")
    return results


if __name__ == "__main__":
    run_distance_analysis()
