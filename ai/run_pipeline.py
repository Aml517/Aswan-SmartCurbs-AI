"""One command for the whole AI engine (Word doc: Camera -> Detection -> Distance -> Virtual bays -> Occupancy -> ANPR -> AI-assisted violations).

Supports four configurable input modes:
  1. file:   Batch offline processing of pre-recorded MP4 (regression tested, backward compatible).
  2. replay: Continuous real-time looping video stream at natural video FPS (simulates live CCTV).
  3. webcam: Live local hardware camera input by device index (e.g. 0).
  4. rtsp:   Live network IP-camera / CCTV stream via RTSP/HTTP URL.

Usage examples:
  python run_pipeline.py --mode file --no-video         # fast regression test on input.mp4
  python run_pipeline.py --mode replay                 # continuous live CCTV simulation
  python run_pipeline.py --mode replay --max-frames 50 # test 50 frames of continuous replay
  python run_pipeline.py --mode webcam --source 0      # live webcam input
  python run_pipeline.py --mode rtsp --source rtsp://ip # live RTSP input
"""
import argparse
import time
from collections import Counter, deque
from pathlib import Path

import cv2
import numpy as np

try:
    from api_client import OccupancyPublisher
    from capture import VideoSource
    from common import CFG, get_homography, path, save_json
    from distance import calculate_all_distances, calculate_frame_distances, describe
    from occupancy import (
        PARKING_SPACES,
        calculate_frame_occupancy,
        draw_parking_spaces,
        process_occupancy_video,
        summarize_spaces,
    )
    from track import INPUT_VIDEO, MODEL_NAME, TRACKER_CONFIG, VEHICLE_CLASSES, load_tracks, process_video
    from violations import detect_violations
    from virtual_bays import estimate_virtual_bays
except ImportError:
    from ai.api_client import OccupancyPublisher
    from ai.capture import VideoSource
    from ai.common import CFG, get_homography, path, save_json
    from ai.distance import calculate_all_distances, calculate_frame_distances, describe
    from ai.occupancy import (
        PARKING_SPACES,
        calculate_frame_occupancy,
        draw_parking_spaces,
        process_occupancy_video,
        summarize_spaces,
    )
    from ai.track import INPUT_VIDEO, MODEL_NAME, TRACKER_CONFIG, VEHICLE_CLASSES, load_tracks, process_video
    from ai.violations import detect_violations
    from ai.virtual_bays import estimate_virtual_bays


def run_file_pipeline(a):
    """Executes the standard batch pipeline on the configured video file (backward compatible)."""
    dets, meta = load_tracks() if a.use_cache else (None, None)
    if dets is None:
        process_video(save_video=not a.no_video)
        dets, meta = load_tracks()
    fps, H = meta["fps"], get_homography()

    if a.anpr or CFG.get("anpr", {}).get("enabled"):
        try:
            from anpr import attach_plates
            dets = attach_plates(dets, INPUT_VIDEO)
        except Exception as e:
            print(f"ANPR skipped: {e}")

    occupancy = process_occupancy_video(dets, save_video=not a.no_video)
    distances = calculate_all_distances(dets, H)
    save_json(distances, path("outputs/distances.json"))
    bays = estimate_virtual_bays(dets, fps)
    save_json(bays, path("outputs/virtual_bays.json"))
    violations = detect_violations(dets, fps, video_path=INPUT_VIDEO, evidence_dir=path("outputs/evidence"))
    save_json(violations, path("outputs/violations.json"))

    if a.api or CFG.get("backend", {}).get("enabled"):
        cfg = dict(CFG)
        cfg["backend"] = dict(CFG.get("backend", {}), enabled=True)
        pub = OccupancyPublisher(cfg)
        for r in occupancy:
            for sid, s in r["spaces"].items():
                pub.update(sid, s["status"], s["confidence"] or 1.0)

    last = occupancy[-1]["capacity"] if occupancy else {}
    summary = {
        "frames": len(dets),
        "fps": fps,
        "calibrated_cm": H is not None,
        "configured_spaces": len(PARKING_SPACES),
        "last_frame_capacity": last,
        "virtual_bays": len(bays["bays"]),
        "violation_candidates": dict(Counter(v["type"] for v in violations)),
    }
    save_json(summary, path("outputs/summary.json"))
    print("\n=== Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")
    if H is None:
        print("Distances are in pixels. Run calibrate.py to get centimetres.")
    if not a.no_video and not a.no_visualize:
        try:
            from visualize import visualize_system
            visualize_system()
        except Exception as e:
            print(f"Visualization skipped: {e}")
    return summary


def run_continuous_stream(a):
    """Executes incremental, real-time streaming for replay, webcam, and RTSP modes."""
    from ultralytics import YOLO

    mode = a.mode or CFG.get("source", {}).get("mode", "replay")
    source_val = a.source
    fps_val = a.fps

    print(f"\n========================================================")
    print(f" Aswan SmartCurbs AI — Continuous Stream Pipeline")
    print(f" Mode: {mode.upper()} | Source: {source_val or 'Default configured'}")
    print(f" Backend Sync: {'ENABLED' if (a.api or CFG.get('backend', {}).get('enabled')) else 'DISABLED'}")
    print(f" Press Ctrl+C in terminal (or 'q' in preview) to stop.")
    print(f"========================================================\n")

    # 1. Open Video Source
    src = VideoSource(mode=mode, source=source_val, target_fps=fps_val)
    src.open()

    # 2. Initialize YOLO Model & Tracker
    model_path = path(MODEL_NAME) if path(MODEL_NAME).exists() else MODEL_NAME
    model = YOLO(str(model_path))
    class_ids = [i for i, n in model.names.items() if n in VEHICLE_CLASSES]

    # 3. Homography & Backend Publisher
    H = get_homography()
    publisher = None
    if a.api or CFG.get("backend", {}).get("enabled"):
        cfg_backend = dict(CFG)
        cfg_backend["backend"] = dict(CFG.get("backend", {}), enabled=True)
        publisher = OccupancyPublisher(cfg_backend)

    # 4. State & Performance Metrics
    rolling_times = deque(maxlen=30)
    start_time = time.time()
    frames_processed = 0
    total_detections_count = 0
    measured_fps = src.fps

    try:
        while True:
            ok, frame, loop_flag = src.read_frame()
            if not ok:
                if src.status in ("eof", "closed"):
                    print(f"\nStream finished (status: {src.status}).")
                break

            frames_processed += 1
            now = time.time()
            rolling_times.append(now)
            if len(rolling_times) > 1:
                measured_fps = (len(rolling_times) - 1) / (rolling_times[-1] - rolling_times[0])

            # Run YOLO + ByteTrack (persist=True maintains tracker state across consecutive frames)
            res = model.track(
                frame,
                persist=True,
                tracker=TRACKER_CONFIG,
                classes=class_ids,
                conf=CFG.get("confidence", 0.35),
                verbose=False,
            )[0]

            dets = []
            if res.boxes is not None and res.boxes.id is not None:
                ids = res.boxes.id.int().cpu().tolist()
                for box, tid in zip(res.boxes, ids):
                    x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
                    name = model.names[int(box.cls[0])]
                    dets.append({
                        "frame_number": src.frame_index,
                        "track_id": int(tid),
                        "class_name": name,
                        "confidence": float(box.conf[0]),
                        "bounding_box": [x1, y1, x2, y2],
                        "center_x": (x1 + x2) / 2,
                        "center_y": (y1 + y2) / 2,
                    })
                    total_detections_count += 1

            # Real-time Occupancy Evaluation
            frame_occ = calculate_frame_occupancy(dets, PARKING_SPACES)
            capacity = summarize_spaces(frame_occ)

            # Debounced Backend Publishing (only stable edge transitions logged)
            if publisher is not None:
                for sid, s in frame_occ.items():
                    publisher.update(sid, s["status"], s["confidence"] or 1.0)

            # Ground Metric Distance Calculation
            frame_dists = calculate_frame_distances(dets, H)
            nearest_gap_label = ""
            if frame_dists:
                best = min(frame_dists, key=lambda d: d["gap_cm"] if d["gap_cm"] is not None else d["distance_pixels"])
                nearest_gap_label = describe(best)

            # Periodic Status Reporting (every 25 frames or loop restart)
            if frames_processed % 25 == 0 or loop_flag or frames_processed == 1:
                loop_str = f" | Loops: {src.loop_count}" if mode == "replay" else ""
                print(
                    f"[{mode.upper()}] Frame {src.frame_index:04d} | "
                    f"FPS: {measured_fps:4.1f} | "
                    f"Tracked: {len(dets)} vehicles | "
                    f"Occupancy: {capacity['occupied']}/{capacity['total']} occupied | "
                    f"Status: {src.status.upper()}{loop_str}"
                )

            # Optional Live GUI Visualization
            if a.show:
                draw_parking_spaces(frame, PARKING_SPACES, frame_occ)
                for d in dets:
                    bx1, by1, bx2, by2 = d["bounding_box"]
                    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        f"{d['class_name']} ID {d['track_id']}",
                        (bx1, max(by1 - 8, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

                banner_txt = (
                    f"{mode.upper()} | FPS: {measured_fps:.1f} | "
                    f"Occ: {capacity['occupied']}/{capacity['total']} | {nearest_gap_label}"
                )
                cv2.rectangle(frame, (0, 0), (frame.shape[1], 35), (20, 20, 20), -1)
                cv2.putText(frame, banner_txt, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

                cv2.imshow("Aswan SmartCurbs AI - Live Video Stream", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("User requested stop via GUI ('q').")
                    break

            if a.max_frames and frames_processed >= a.max_frames:
                print(f"Reached requested limit of {a.max_frames} frames. Stopping.")
                break

    except KeyboardInterrupt:
        print("\nShutdown signal (Ctrl+C) received. Stopping cleanly...")
    finally:
        src.release()
        if a.show:
            cv2.destroyAllWindows()

    elapsed = max(time.time() - start_time, 0.001)
    overall_fps = frames_processed / elapsed
    print("\n=== Stream Processing Summary ===")
    print(f"Mode: {mode}")
    print(f"Frames Processed: {frames_processed}")
    print(f"Elapsed Time: {elapsed:.2f}s")
    print(f"Average Measured FPS: {overall_fps:.1f}")
    if mode == "replay":
        print(f"Replay Loops Completed: {src.loop_count}")
    if publisher is not None:
        print(f"Backend Occupancy Updates Sent: {publisher.updates_sent}")
    print("==================================\n")

    return {
        "mode": mode,
        "frames_processed": frames_processed,
        "elapsed_sec": round(elapsed, 2),
        "average_fps": round(overall_fps, 2),
        "loop_count": src.loop_count,
        "updates_sent": publisher.updates_sent if publisher else 0,
    }


def main():
    ap = argparse.ArgumentParser(description="Aswan SmartCurbs AI Pipeline Controller")
    ap.add_argument("--mode", choices=["file", "replay", "webcam", "rtsp", "windy"], default=None,
                    help="Input source mode: file, replay, webcam, rtsp, windy")
    ap.add_argument("--source", type=str, default=None,
                    help="Custom source override: video path, webcam index (0), or RTSP URL")
    ap.add_argument("--max-frames", type=int, default=None,
                    help="Maximum frames to process before stopping (useful for tests)")
    ap.add_argument("--fps", type=float, default=None,
                    help="Target replay/streaming FPS")
    ap.add_argument("--show", action="store_true",
                    help="Show live OpenCV rendering window")
    ap.add_argument("--use-cache", action="store_true",
                    help="Reuse cached tracks.json (file mode only)")
    ap.add_argument("--no-video", action="store_true",
                    help="Skip saving intermediate video files (file mode only)")
    ap.add_argument("--no-visualize", action="store_true",
                    help="Skip generating final video file")
    ap.add_argument("--anpr", action="store_true",
                    help="Enable ANPR plate recognition (file mode)")
    ap.add_argument("--api", action="store_true",
                    help="Send occupancy updates to backend API")

    a = ap.parse_args()

    # Determine mode
    resolved_mode = a.mode or CFG.get("source", {}).get("mode", "file")

    if resolved_mode == "file":
        return run_file_pipeline(a)
    else:
        a.mode = resolved_mode
        return run_continuous_stream(a)


if __name__ == "__main__":
    main()
