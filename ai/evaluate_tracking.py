"""Tracking quality report from the cached outputs/tracks.json (no model run needed).

Flags (a) very short tracks and (b) *possible ID switches*: a track that ends and another track of the same
class that starts within a few frames, at about the same place. Those are one vehicle that got two IDs.
Writes outputs/tracking_quality.json.
"""
import argparse
from collections import defaultdict

from common import load_json, path, save_json


def analyse(tracks_json, short_seconds=1.0, max_gap_frames=25, max_dist_ratio=0.75):
    data = load_json(tracks_json)
    fps = data.get("fps") or 25.0
    tracks = defaultdict(list)
    for fi, dets in enumerate(data["frames"]):
        for d in dets:
            tracks[d["track_id"]].append((fi, d))
    info = {}
    for tid, rows in tracks.items():
        first, last = rows[0], rows[-1]
        info[tid] = {"track_id": tid, "class": first[1]["class_name"], "start": first[0], "end": last[0],
                     "frames": len(rows), "start_c": (first[1]["center_x"], first[1]["center_y"]),
                     "end_c": (last[1]["center_x"], last[1]["center_y"]),
                     "width": first[1]["bounding_box"][2] - first[1]["bounding_box"][0]}
    n_frames = len(data["frames"])
    short = [t for t in info.values() if t["frames"] < short_seconds * fps]
    switches = []
    for a in info.values():
        if a["end"] >= n_frames - 1:        # still alive at the end of the video
            continue
        for b in info.values():
            if b["track_id"] == a["track_id"] or b["class"] != a["class"]:
                continue
            gap = b["start"] - a["end"]
            if 0 <= gap <= max_gap_frames:
                dist = ((a["end_c"][0] - b["start_c"][0]) ** 2 + (a["end_c"][1] - b["start_c"][1]) ** 2) ** 0.5
                if dist <= max_dist_ratio * max(a["width"], 1):
                    switches.append({"old_id": a["track_id"], "new_id": b["track_id"], "gap_frames": gap,
                                     "distance_px": round(dist, 1)})
    long_tracks = [t for t in info.values() if t["frames"] >= n_frames * 0.9]
    return {
        "frames": n_frames, "fps": fps, "unique_track_ids": len(info),
        "tracks_alive_90pct_of_video": [t["track_id"] for t in long_tracks],
        "short_tracks_under_%ss" % short_seconds: [{"track_id": t["track_id"], "frames": t["frames"]} for t in short],
        "short_track_ratio": round(len(short) / len(info), 3) if info else 0,
        "possible_id_switches": switches,
        "possible_id_switch_count": len(switches),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracks", default=str(path("outputs/tracks.json")))
    ap.add_argument("--out", default=str(path("outputs/tracking_quality.json")))
    a = ap.parse_args()
    report = analyse(a.tracks)
    save_json(report, a.out)
    print({k: v for k, v in report.items() if k != "possible_id_switches"})
    for s in report["possible_id_switches"]:
        print("  possible ID switch:", s)
    print("saved", a.out)
