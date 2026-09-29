"""AI-assisted violation candidates (Word doc section 6).

Workflow required by the doc:  AI detection -> evidence -> admin/inspector review -> official action.
This module ONLY produces candidates (status 'pending_review', official_action False). It never issues a fine.
"""
from pathlib import Path

import cv2

from common import CFG, get_homography, point_in_polygon
from distance import curb_distance_cm, nearest_gap_cm
from virtual_bays import group_tracks, parked_runs

LABELS = {"overstay": "Overstay", "restricted_zone_parking": "Restricted-zone parking", "improper_parking": "Improper parking",
          "blocking_access": "Blocking access", "outside_bay": "Outside configured bay", "unauthorized_vehicle": "Unauthorized vehicle"}


def _ground_point(d):
    return (d["center_x"], d["bounding_box"][3])


def _evidence(video_path, evidence_dir, frame_number, det, kind, index):
    if not video_path or not evidence_dir:
        return None
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number - 1)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    x1, y1, x2, y2 = det["bounding_box"]
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
    cv2.putText(frame, f"{LABELS[kind]} - track {det['track_id']} - frame {frame_number}", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    Path(evidence_dir).mkdir(parents=True, exist_ok=True)
    target = Path(evidence_dir) / f"violation_{index:03d}_{kind}_track{det['track_id']}.jpg"
    cv2.imwrite(str(target), frame)
    return target.name


def detect_violations(all_detections, fps, cfg=CFG, video_path=None, evidence_dir=None):
    H = get_homography(cfg)
    zone, t = cfg["zone"], cfg["thresholds"]
    limit_s = zone.get("overstay_demo_seconds") or (zone["max_stay_minutes"] * 60 if zone.get("max_stay_minutes") else None)
    frames = {f[0]["frame_number"]: f for f in all_detections if f}
    authorized = {p.replace(" ", "") for p in cfg.get("authorized_plates", [])}
    found = []

    def add(kind, run, note):
        det = run[-1]
        found.append({"type": kind, "label": LABELS[kind], "track_id": det["track_id"], "frame_number": det["frame_number"],
                      "time_seconds": round(det["frame_number"] / fps, 2),
                      "confidence": round(sum(d["confidence"] for d in run) / len(run), 3), "note": note,
                      "plate": det.get("plate"), "status": "pending_review", "official_action": False,
                      "workflow": "AI detection -> evidence -> admin/inspector review -> official action",
                      "_det": det})

    for tid, run in parked_runs(all_detections, fps, cfg).items():
        last = run[-1]
        dwell = (run[-1]["frame_number"] - run[0]["frame_number"]) / fps
        ground = _ground_point(last)
        if any(point_in_polygon(ground, a) for a in cfg.get("restricted_areas", [])):
            add("restricted_zone_parking", run, "Vehicle parked inside a restricted area.")
        if any(point_in_polygon(ground, a) for a in cfg.get("protected_access_areas", [])):
            add("blocking_access", run, "Vehicle parked inside a protected access area.")
        if limit_s and dwell > limit_s:
            add("overstay", run, f"Observed parked {dwell:.0f}s; limit {limit_s:.0f}s (observed dwell time, not a payment session).")
        curb = curb_distance_cm(last, cfg, H)
        gap = nearest_gap_cm(last, frames.get(last["frame_number"], []), H)
        if (curb is not None and curb > t["max_curb_distance_cm"]) or (gap is not None and gap < t["min_gap_cm"]):
            add("improper_parking", run, f"Distance to curb: {curb} cm; nearest gap: {gap} cm.")
        if cfg.get("enforce_configured_bays") and cfg["parking_spaces"] and not any(
                point_in_polygon(ground, p) for p in cfg["parking_spaces"].values()):
            add("outside_bay", run, "Parked outside every configured bay.")
        plate = (last.get("plate") or "").replace(" ", "")
        if authorized and plate and plate not in authorized:
            add("unauthorized_vehicle", run, f"Plate {plate} is not in the authorized list.")

    for i, v in enumerate(found, 1):
        v["id"] = i
        v["evidence_image"] = _evidence(video_path, evidence_dir, v["frame_number"], v.pop("_det"), v["type"], i)
    return found
