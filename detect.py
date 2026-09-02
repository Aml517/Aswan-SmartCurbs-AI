import logging
from pathlib import Path
from typing import List, Dict, Any

import cv2
from ultralytics import YOLO
from tqdm import tqdm  # Used to display a professional progress bar in the console

# Define project constants and file paths
INPUT_VIDEO = Path("data/input.mp4")
MODEL_NAME = "yolov8n.pt"
VEHICLE_CLASSES = {"car", "bus", "truck", "motorcycle"}

# 1. Configure the logging system (Logging is preferred over print for production apps)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class VehicleDetector:
    """
    A specialized class for vehicle detection using YOLOv8.
    Designed for easy integration into larger AI systems.
    """
    def __init__(self, model_name: str = "yolov8n.pt", conf_threshold: float = 0.25):
        """Initialize the model and set detection parameters."""
        self.model = YOLO(model_name)
        self.conf_threshold = conf_threshold
        
        # Define target class IDs for faster processing:
        # Based on COCO dataset IDs: 2: car, 3: motorcycle, 5: bus, 7: truck
        self.target_classes = [2, 3, 5, 7] 

    def _extract_detections(self, results) -> List[Dict[str, Any]]:
        """Convert raw YOLO output into a clean, structured dictionary format."""
        detections = []
        boxes = results[0].boxes # Get bounding box results from the first image in batch
        
        for box in boxes:
            cls_id = int(box.cls[0])
            # Only process objects that belong to our target vehicle classes
            if cls_id in self.target_classes:
                x1, y1, x2, y2 = map(int, box.xyxy[0]) # Get coordinates
                detections.append({
                    "class_id": cls_id,
                    "class_name": self.model.names[cls_id],
                    "confidence": float(box.conf[0]),
                    "bbox": (x1, y1, x2, y2)
                })
        return detections

    def annotate_frame(self, frame, detections: List[Dict]):
        """Draw bounding boxes and labels on the frame for visualization."""
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = f"{det['class_name']} {det['confidence']:.2f}"
            
            # Draw the bounding box (Green)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            # Draw the label background and text
            cv2.putText(frame, label, (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        return frame

    def process_video(self, input_path: str, output_path: str):
        """Main processor that reads input video and saves the annotated results."""
        input_path = Path(input_path)
        if not input_path.exists():
            logger.error(f"Video not found: {input_path}")
            return

        # Initialize Video Capture to read the file
        cap = cv2.VideoCapture(str(input_path))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Ensure the output directory exists
        # Fix: Ensure we are saving to a video file, not just a folder
        output_file_path = str(output_path)
        if not output_file_path.endswith('.mp4'):
            output_file_path = str(Path(output_path) / "result.mp4")

        Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)
        # Initialize Video Writer to save the output file
        writer = cv2.VideoWriter(output_file_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

        logger.info(f"Starting processing: {input_path.name}")
        # 2. Add Progress Bar (A professional touch for long-running tasks)
        for _ in tqdm(range(total_frames), desc="Processing Frames"):
            success, frame = cap.read()
            if not success:
                break

            # Execute AI detection on the current frame
            # verbose=False keeps the console clean by hiding internal YOLO logs
            results = self.model.predict(frame, conf=self.conf_threshold, verbose=False)
            detections = self._extract_detections(results)
            
            # Draw detections onto the frame
            annotated_frame = self.annotate_frame(frame, detections)
            
            # Save the processed frame to the output video file
            writer.write(annotated_frame)

        # Cleanup resources
        cap.release()
        writer.release()
        logger.info(f"Output saved to: {output_path}")

# --- Main Execution Block ---
if __name__ == "__main__":
    # Script settings (Can be moved to a config.yaml file later)
    CONFIG = {
        "input": "data/input.mp4",
        "output": "outputs",
        "model": "yolov8n.pt"
    }

    # Initialize the detector and start video processing
    detector = VehicleDetector(model_name=CONFIG["model"])
    detector.process_video(CONFIG["input"], CONFIG["output"])