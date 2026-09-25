"""One command for the whole AI engine (Word doc: Camera -> Detection -> Distance -> Virtual bays -> Occupancy -> ANPR -> AI-assisted violations).

  python run_pipeline.py                # track once, then occupancy + distances + virtual bays + violations + final video
  python run_pipeline.py --use-cache    # reuse outputs/tracks.json (no AI model run)
  python run_pipeline.py --no-video     # data only (fast)
  python run_pipeline.py --anpr         # also read number plates (needs easyocr)
  python run_pipeline.py --api          # also push occupancy to the Slotiq backend
"""
import argparse
from collections import Counter

from api_client import OccupancyPublisher
from common import CFG, get_homography, path, save_json
from distance import calculate_all_distances
from occupancy import PARKING_SPACES, process_occupancy_video
from track import INPUT_VIDEO, load_tracks, process_video
from violations import detect_violations
from virtual_bays import estimate_virtual_bays


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-cache", action="store_true")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--anpr", action="store_true")
    ap.add_argument("--api", action="store_true")
    a = ap.parse_args()

    dets, meta = load_tracks() if a.use_cache else (None, None)
    if dets is None:
        process_video(save_video=not a.no_video)
        dets, meta = load_tracks()
    fps, H = meta["fps"], get_homography()

    if a.anpr or CFG["anpr"]["enabled"]:
        from anpr import attach_plates
        dets = attach_plates(dets, INPUT_VIDEO)

    occupancy = process_occupancy_video(dets, save_video=not a.no_video)
    distances = calculate_all_distances(dets, H)
    save_json(distances, path("outputs/distances.json"))
    bays = estimate_virtual_bays(dets, fps)
    save_json(bays, path("outputs/virtual_bays.json"))
    violations = detect_violations(dets, fps, video_path=INPUT_VIDEO, evidence_dir=path("outputs/evidence"))
    save_json(violations, path("outputs/violations.json"))

    if a.api or CFG["backend"]["enabled"]:
        cfg = dict(CFG); cfg["backend"] = dict(CFG["backend"], enabled=True)
        pub = OccupancyPublisher(cfg)
        for r in occupancy:
            for sid, s in r["spaces"].items():
                pub.update(sid, s["status"], s["confidence"] or 1.0)

    last = occupancy[-1]["capacity"] if occupancy else {}
    summary = {"frames": len(dets), "fps": fps, "calibrated_cm": H is not None, "configured_spaces": len(PARKING_SPACES),
               "last_frame_capacity": last, "virtual_bays": len(bays["bays"]),
               "violation_candidates": dict(Counter(v["type"] for v in violations))}
    save_json(summary, path("outputs/summary.json"))
    print("\n=== Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")
    if H is None:
        print("Distances are in pixels. Run calibrate.py to get centimetres.")
    if not a.no_video:
        from visualize import visualize_system
        visualize_system()


if __name__ == "__main__":
    main()
