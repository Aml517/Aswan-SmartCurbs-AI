"""Write the agreed-format JSON files from the cached pipeline outputs (no model run needed).

  outputs/contract_frames.json          Detection -> Occupancy   (list of frame messages)
  outputs/contract_zone_occupancy.json  Occupancy -> Backend     (list of zone payloads, one per frame)
"""
from common import CFG, load_json, path, save_json
from contracts import frames_from_tracks, validate_zone_payload, zone_payload
from occupancy import calculate_all_occupancy
from track import load_tracks


def main():
    dets, meta = load_tracks()
    if dets is None:
        raise SystemExit("outputs/tracks.json not found - run track.py first.")
    fps = meta["fps"]
    save_json(frames_from_tracks(dets, fps), path("outputs/contract_frames.json"))
    backend = CFG.get("backend", {})
    zone_id, space_map = int(backend.get("zone_id", 1)), backend.get("space_map", {})
    payloads = [zone_payload(zone_id, r["spaces"], space_map) for r in calculate_all_occupancy(dets)]
    bad = [(i, e) for i, p in enumerate(payloads) for e in validate_zone_payload(p)]
    if bad:
        raise SystemExit(f"invalid payloads: {bad[:5]}")
    save_json(payloads, path("outputs/contract_zone_occupancy.json"))
    print(f"frames: {len(dets)}  payloads: {len(payloads)}  (all valid)")


if __name__ == "__main__":
    main()
