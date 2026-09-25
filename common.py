"""Shared helpers: configuration, geometry, calibration and JSON I/O.

Every path is resolved from the location of this file, so scripts work from any folder.
Layout:  ai/vehicle_detection/{src, data, outputs, notebooks, config.json}
"""
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"


def load_config(path=CONFIG_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg, path=CONFIG_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


CFG = load_config()


def path(relative):
    """Resolve a config path (e.g. 'data/input.mp4') against the module root."""
    return ROOT / relative


def save_json(data, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(source):
    with open(source, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- geometry
def iou(a, b):
    """Intersection-over-union of two boxes (x1, y1, x2, y2)."""
    ix1, iy1, ix2, iy2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def point_in_polygon(point, polygon):
    poly = np.asarray(polygon, dtype=np.int32)
    return cv2.pointPolygonTest(poly, (float(point[0]), float(point[1])), False) >= 0


def _point_segment(p, a, b):
    p, a, b = np.asarray(p, float), np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    t = 0.0 if not ab.any() else float(np.clip(np.dot(p - a, ab) / np.dot(ab, ab), 0, 1))
    return float(np.linalg.norm(p - (a + t * ab)))


def _ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def segment_distance(a1, a2, b1, b2):
    """Minimum distance between segments A and B (0 if they cross)."""
    if _ccw(a1, b1, b2) != _ccw(a2, b1, b2) and _ccw(a1, a2, b1) != _ccw(a1, a2, b2):
        return 0.0
    return min(_point_segment(a1, b1, b2), _point_segment(a2, b1, b2),
               _point_segment(b1, a1, a2), _point_segment(b2, a1, a2))


def point_line_distance(p, a, b):
    """Perpendicular distance from point p to the infinite line through a and b."""
    a, b, p = np.asarray(a, float), np.asarray(b, float), np.asarray(p, float)
    d = b - a
    n = np.linalg.norm(d)
    return float(abs(d[0] * (p[1] - a[1]) - d[1] * (p[0] - a[0])) / n) if n else float(np.linalg.norm(p - a))


# ------------------------------------------------------------- calibration
def get_homography(cfg=None):
    """Image -> ground-plane (centimetres) homography, or None when not calibrated.

    Needs 4 image points and the same 4 points in real-world cm (see calibrate.py).
    Without it the system reports pixels only.
    """
    c = (cfg or CFG).get("calibration", {})
    if not c.get("enabled") or len(c.get("image_points", [])) < 4:
        return None
    H, _ = cv2.findHomography(np.float32(c["image_points"]), np.float32(c["world_points_cm"]))
    return H


def to_ground(H, point):
    v = H @ np.array([point[0], point[1], 1.0])
    return (float(v[0] / v[2]), float(v[1] / v[2]))
