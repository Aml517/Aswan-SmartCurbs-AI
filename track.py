"""Vehicle tracking with YOLO + ByteTrack. Every vehicle keeps one ID across frames.

The full result is cached in outputs/tracks.json so the other modules
(occupancy, distance, virtual bays, violations) never need to re-run the AI model.
"""
from pathlib import Path

import cv2

from common import CFG, load_json, path, save_json
from detect import INPUT_VIDEO, MODEL_NAME, VEHICLE_CLASSES

TRACKER_CONFIG = CFG["tracker"]
TRACK_OUTPUT_VIDEO = path("outputs/vehicle_tracking_output.mp4")
TRACKS_JSON = path("outputs/tracks.json")


def process_video(input_path=INPUT_VIDEO, output_path=TRACK_OUTPUT_VIDEO, model_name=MODEL_NAME,
                  save_video=True, cache_path=TRACKS_JSON):
    """Track vehicles in a video.

    Returns: list (one item per frame) of detection dicts:
      frame_number (1-based), track_id, class_name, confidence, bounding_box [x1,y1,x2,y2], center_x, center_y
    """
    from ultralytics import YOLO
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")
    model = YOLO(model_name)
    class_ids = [i for i, n in model.names.items() if n in VEHICLE_CLASSES]
    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open input video: {input_path}")
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    writer = None
    if save_video:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    all_detections, n = [], 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            n += 1
            res = model.track(frame, persist=True, tracker=TRACKER_CONFIG, classes=class_ids,
                              conf=CFG["confidence"], verbose=False)[0]
            dets = []
            if res.boxes is not None and res.boxes.id is not None:
                ids = res.boxes.id.int().cpu().tolist()
                for box, tid in zip(res.boxes, ids):
                    x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
                    name = model.names[int(box.cls[0])]
                    dets.append({"frame_number": n, "track_id": int(tid), "class_name": name,
                                 "confidence": float(box.conf[0]), "bounding_box": [x1, y1, x2, y2],
                                 "center_x": (x1 + x2) / 2, "center_y": (y1 + y2) / 2})
                    if writer is not None:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, f"{name} ID {tid}", (x1, max(y1 - 10, 20)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
            all_detections.append(dets)
            if writer is not None:
                writer.write(frame)
    finally:
        cap.release()
        if writer is not None:
            writer.release()
    if cache_path:
        save_json({"video": str(input_path), "fps": fps, "width": w, "height": h, "frames": all_detections}, cache_path)
    print(f"Tracked {n} frames -> {cache_path}")
    return all_detections


def load_tracks(cache_path=TRACKS_JSON):
    """Load the cached tracking result. Returns (all_detections, meta) or (None, None)."""
    if not Path(cache_path).exists():
        return None, None
    data = load_json(cache_path)
    return data["frames"], {k: data[k] for k in ("video", "fps", "width", "height")}


if __name__ == "__main__":
    process_video()
