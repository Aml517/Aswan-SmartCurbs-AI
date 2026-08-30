import sys
from pathlib import Path

import cv2
from ultralytics import YOLO

# Ensure the script can locate modules in the same directory
sys.path.append(str(Path(__file__).parent))

# Import shared configuration constants from the detection module
from detect import (
	INPUT_VIDEO,
	MODEL_NAME,
	VEHICLE_CLASSES,
)

# Configuration for the ByteTrack algorithm used by YOLO
TRACKER_CONFIG = "bytetrack.yaml"
TRACK_OUTPUT_VIDEO = Path(
	"ai/vehicle_detection/outputs/vehicle_tracking_output.mp4"
)


def _vehicle_class_ids(model_names):
	"""
	Filter the model's full class list to extract only the IDs 
	corresponding to vehicle types (car, bus, truck, motorcycle).
	"""
	if isinstance(model_names, dict):
		return [
			class_id
			for class_id, class_name in model_names.items()
			if class_name in VEHICLE_CLASSES
		]

	return [
		class_id
		for class_id, class_name in enumerate(model_names)
		if class_name in VEHICLE_CLASSES
	]


def process_video(input_path=INPUT_VIDEO, output_path=TRACK_OUTPUT_VIDEO):
	"""
	Main processing pipeline: Reads video, performs object tracking, 
	annotates frames with IDs, and saves the output.
	"""
	input_path = Path(input_path)
	output_path = Path(output_path)

	# Validate input file existence
	if not input_path.exists():
		raise FileNotFoundError(f"Input video not found: {input_path}")

	# Initialize YOLO model and determine target class indices
	model = YOLO(MODEL_NAME)
	vehicle_class_ids = _vehicle_class_ids(model.names)
	capture = cv2.VideoCapture(str(input_path))

	if not capture.isOpened():
		raise RuntimeError(f"Could not open input video: {input_path}")

	# Retrieve video metadata for the VideoWriter setup
	width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
	height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
	fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
	
	# Create output directory structure
	output_path.parent.mkdir(parents=True, exist_ok=True)
	
	# Initialize the output video stream
	writer = cv2.VideoWriter(
		str(output_path),
		cv2.VideoWriter_fourcc(*"mp4v"),
		fps,
		(width, height),
	)

	if not writer.isOpened():
		capture.release()
		raise RuntimeError(f"Could not create output video: {output_path}")

	all_detections = [] # Store tracking data for all frames
	frame_number = 0

	try:
		while True:
			success, frame = capture.read()
			if not success:
				break

			frame_number += 1
			
			# Execute the tracker on the current frame. 
			# persist=True allows the model to remember IDs across frames.
			result = model.track(
				frame,
				persist=True,
				tracker=TRACKER_CONFIG,
				classes=vehicle_class_ids,
				verbose=False,
			)[0]
			
			boxes = result.boxes
			frame_detections = []

			# Check if any objects were successfully tracked
			if boxes is not None and boxes.id is not None:
				# Extract tracking IDs assigned by ByteTrack
				track_ids = boxes.id.int().cpu().tolist()

				for box_index, box in enumerate(boxes):
					class_id = int(box.cls[0])
					class_name = model.names[class_id]
					
					# Double check that the object belongs to our target classes
					if class_name not in VEHICLE_CLASSES:
						continue

					# Get bounding box coordinates
					x1, y1, x2, y2 = (
						int(value) for value in box.xyxy[0].tolist()
					)
					
					confidence = float(box.conf[0])
					track_id = int(track_ids[box_index])
					
					# Store rich metadata including the centroid of the vehicle
					frame_detections.append(
						{
							"frame_number": frame_number,
							"track_id": int(track_id),
							"class_name": class_name,
							"confidence": float(confidence),
							"bounding_box": [x1, y1, x2, y2],
							"center_x": (x1 + x2) / 2, # Centroid X
							"center_y": (y1 + y2) / 2, # Centroid Y
						}
					)
					
					# Create visual label for the frame
					label = (
						f"{class_name} ID: {track_id} "
						f"Conf: {confidence:.2f}"
					)
					
					# Draw green rectangle and text label on the current frame
					cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
					cv2.putText(
						frame,
						label,
						(x1, max(y1 - 10, 20)),
						cv2.FONT_HERSHEY_SIMPLEX,
						0.55,
						(0, 255, 0),
						2,
					)

			all_detections.append(frame_detections)
			writer.write(frame) # Save the annotated frame to disk
			
	finally:
		# Always release system resources regardless of success/failure
		capture.release()
		writer.release()

	print(f"Processed tracking video saved to: {output_path}")
	return all_detections


if __name__ == "__main__":
	# Execute the tracking process
	all_detections = process_video()