"""Vehicle-to-vehicle distance and curb analysis (Word doc 5.2).

Goal from the supervisor: "Car A - 82 cm - Car B".
  * Calibrated (config.json -> calibration.enabled, made by calibrate.py): the bottom edge of each
    vehicle box is projected onto the ground plane and the gap is measured in centimetres.
  * Not calibrated: only pixel distances are reported. Nothing is ever shown as cm without calibration.
"""
import math

from common import CFG, get_homography, point_line_distance, segment_distance, to_ground, save_json, path
from track import load_tracks, process_video


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


def describe(d):
    """Human-readable label: 'Car 3 - 82 cm - Car 5' (or pixels when uncalibrated)."""
    if d["gap_cm"] is not None:
        return f"Car {d['vehicle_1_id']} - {d['gap_cm']:.0f} cm - Car {d['vehicle_2_id']}"
    return f"Car {d['vehicle_1_id']} - {d['distance_pixels']:.0f} px (uncalibrated) - Car {d['vehicle_2_id']}"


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
