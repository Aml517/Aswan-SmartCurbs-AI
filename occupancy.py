from pathlib import Path
from typing import Any
import json
import cv2
import numpy as np

# Import global constants and the tracking engine from the track module
from track import INPUT_VIDEO, process_video

# --- Spatial Configuration ---
# Defining trapezoidal polygons for each parking slot.
# These coordinates represent the perspective of the camera in the physical scene.
# Format: {Space_ID: [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]}
PARKING_SPACES: dict[int, list[tuple[int, int]]] = {
    1: [(0, 360), (116, 360), (169, 286), (0, 286)],
    2: [(0, 286), (169, 286), (218, 238), (42, 238)],
    # Slot 3 is currently disabled/commented out
    4: [(94, 187), (269, 187), (313, 137), (145, 137)],
    5: [(145, 137), (313, 137), (330, 91), (203, 91)],
}

# Define where the annotated video will be stored
OCCUPANCY_OUTPUT_VIDEO = Path(
    "ai/vehicle_detection/outputs/parking_occupancy_output.mp4"
)

def is_vehicle_in_parking_space(
    vehicle: dict[str, Any],
    parking_polygon: list[tuple[int, int]],
) -> bool:
    """
    Determine if a vehicle's center point is located within a defined parking polygon.
    Uses OpenCV's pointPolygonTest for geometric validation.
    """
    point = (float(vehicle["center_x"]), float(vehicle["center_y"]))
    # Convert polygon coordinates to a NumPy array for OpenCV processing
    polygon = np.asarray(parking_polygon, dtype=np.int32)
    
    # Returns True if point is inside or on the edge of the polygon
    return cv2.pointPolygonTest(polygon, point, False) >= 0


def calculate_frame_occupancy(
    frame_detections: list[dict[str, Any]],
    parking_spaces: dict[int, list[tuple[int, int]]] = PARKING_SPACES,
) -> dict[int, dict[str, Any]]:
    """
    Analyze all detections in a single frame to determine which slots are Free vs Occupied.
    """
    # Initialize all spaces as 'Free' by default
    occupancy = {
        space_id: {"status": "Free", "vehicle_id": None}
        for space_id in parking_spaces
    }

    for space_id, polygon in parking_spaces.items():
        # Identify all vehicles whose centers fall into this specific polygon
        vehicles_in_space = [
            vehicle
            for vehicle in frame_detections
            if is_vehicle_in_parking_space(vehicle, polygon)
        ]
        
        if vehicles_in_space:
            # If multiple vehicles overlap the space, select the one with highest AI confidence
            vehicle = max(
                vehicles_in_space,
                key=lambda detection: float(detection["confidence"]),
            )
            occupancy[space_id] = {
                "status": "Occupied",
                "vehicle_id": int(vehicle["track_id"]),
            }

    return occupancy


def calculate_all_occupancy(
    all_detections: list[list[dict[str, Any]]],
    parking_spaces: dict[int, list[tuple[int, int]]] = PARKING_SPACES,
) -> list[dict[str, Any]]:
    """
    Iterate through the entire video detection history to map occupancy over time.
    """
    results = []
    for fallback_frame_number, frame_detections in enumerate(all_detections, 1):
        # Extract the specific frame number if available, else use the loop index
        frame_number = (
            frame_detections[0].get("frame_number", fallback_frame_number)
            if frame_detections
            else fallback_frame_number
        )
        
        results.append(
            {
                "frame_number": frame_number,
                "spaces": calculate_frame_occupancy(
                    frame_detections, parking_spaces
                ),
            }
        )
    return results


def draw_parking_spaces(
    frame: np.ndarray,
    parking_spaces: dict[int, list[tuple[int, int]]],
    occupancy: dict[int, dict[str, Any]],
) -> np.ndarray:
    """
    Render the parking layout onto the video frame.
    Green = Free Space | Red = Occupied Space.
    """
    for space_id, polygon in parking_spaces.items():
        space_result = occupancy[space_id]
        is_occupied = space_result["status"] == "Occupied"
        
        # Color Logic: Red for Occupied, Green for Free
        color = (0, 0, 255) if is_occupied else (0, 255, 0)
        
        points = np.asarray(polygon, dtype=np.int32)
        # Draw the polygon boundaries
        cv2.polylines(frame, [points], True, color, 2)
        
        # Create UI labels for the space status
        label = f"Space {space_id}: {space_result['status']}"
        if is_occupied:
            label += f" ID {space_result['vehicle_id']}"
            
        # Place text at the first vertex of the polygon
        text_position = tuple(points[0]) if len(points) else (10, 30)
        cv2.putText(
            frame,
            label,
            text_position,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )
    return frame


def process_occupancy_video(
    output_path: Path = OCCUPANCY_OUTPUT_VIDEO,
) -> list[dict[str, Any]]:
    """
    Execution Pipeline: 
    1. Run Tracking -> 2. Calculate Spatial Occupancy -> 3. Render Output Video.
    """
    # Step 1: Run the AI tracking module
    all_detections = process_video()
    
    # Step 2: Perform spatial geometry analysis
    occupancy_results = calculate_all_occupancy(
        all_detections, PARKING_SPACES
    )

    # Step 3: Video Rendering and File Export
    capture = cv2.VideoCapture(str(INPUT_VIDEO))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open input video: {INPUT_VIDEO}")

    # Configure VideoWriter settings
    output_path = Path(output_path)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    
    # Create directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    
    if not writer.isOpened():
        capture.release()
        raise RuntimeError(f"Could not create output video: {output_path}")

    try:
        # Loop through every frame to draw occupancy UI
        for frame_result in occupancy_results:
            success, frame = capture.read()
            if not success:
                break
            
            draw_parking_spaces(
                frame, PARKING_SPACES, frame_result["spaces"]
            )
            writer.write(frame)
    finally:
        # Resource cleanup
        capture.release()
        writer.release()

    # Final Summary Logging
    for frame_result in occupancy_results:
        for space_id, space_result in frame_result["spaces"].items():
            print(f"Frame {frame_result['frame_number']}")
            print(f"Space {space_id} -> {space_result['status']}")
            if space_result["vehicle_id"] is not None:
                print(f"Vehicle ID -> {space_result['vehicle_id']}")

    print(f"Occupancy video saved to: {output_path}")
    return occupancy_results


# --- Entry Point ---
if __name__ == "__main__":
    # 1. Process video and get occupancy data
    occupancy_results = process_occupancy_video()
    
    # 2. Export the final results to a JSON file for Dashboard/API integration
    output_json_path = Path("ai/vehicle_detection/outputs/occupancy_results.json")
    
    with open(output_json_path, "w") as f:
        json.dump(occupancy_results, f, indent=4)
        
    print(f"\n[DONE] AI Predictions saved to: {output_json_path}")