"""Vehicle detection with YOLO (Word doc 5.1: Camera -> Vehicle Detection)."""
import logging
from pathlib import Path
from typing import Any, Dict, List

import cv2

from common import CFG, path

INPUT_VIDEO = path(CFG["video"])
MODEL_NAME = CFG["model"]
VEHICLE_CLASSES = set(CFG["vehicle_classes"])
DETECT_OUTPUT_VIDEO = path("outputs/vehicle_detection_output.mp4")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def extract_vehicle_detections(result, names, allowed=VEHICLE_CLASSES) -> List[Dict[str, Any]]:
    """Convert one YOLO result into a list of plain dicts (vehicles only)."""
    detections = []
    if result.boxes is None:
        return detections
    for box in result.boxes:
        class_id = int(box.cls[0])
        class_name = names[class_id]
        if class_name not in allowed:
            continue
        x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
        detections.append({
            "class_id": class_id, "class_name": class_name, "confidence": float(box.conf[0]),
            "x1": x1, "y1": y1, "x2": x2, "y2": y2, "bbox": (x1, y1, x2, y2),
        })
    return detections


class VehicleDetector:
    """YOLO wrapper for single-frame detection (used by the notebook and other modules)."""

    def __init__(self, model_name=MODEL_NAME, conf_threshold=CFG["confidence"]):
        from ultralytics import YOLO  # imported here so the module loads without the AI stack
        self.model = YOLO(model_name)
        self.conf_threshold = conf_threshold

    def detect(self, frame):
        result = self.model.predict(frame, conf=self.conf_threshold, verbose=False)[0]
        return extract_vehicle_detections(result, self.model.names)

    @staticmethod
    def annotate_frame(frame, detections):
        for d in detections:
            cv2.rectangle(frame, (d["x1"], d["y1"]), (d["x2"], d["y2"]), (0, 255, 0), 2)
            cv2.putText(frame, f"{d['class_name']} {d['confidence']:.2f}", (d["x1"], max(d["y1"] - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame

    def process_video(self, input_path=INPUT_VIDEO, output_path=DETECT_OUTPUT_VIDEO):
        input_path, output_path = Path(input_path), Path(output_path)
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise FileNotFoundError(f"Could not open video: {input_path}")
        w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
        try:
            from tqdm import tqdm
            frames = tqdm(range(total), desc="Detecting")
        except ImportError:
            frames = range(total)
        for _ in frames:
            ok, frame = cap.read()
            if not ok:
                break
            writer.write(self.annotate_frame(frame, self.detect(frame)))
        cap.release(); writer.release()
        logger.info("Saved: %s", output_path)


if __name__ == "__main__":
    VehicleDetector().process_video()
