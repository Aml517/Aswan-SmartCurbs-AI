import math
import logging
from typing import Any, List, Dict
from pathlib import Path

# Import the processing function from the tracking module
from track import process_video

# --- Global System Settings (Constants) ---
# Conversion factor: How many meters per pixel.
# This must be calibrated based on the camera's perspective/angle in Aswan.
# A value of 0.02 means approximately every 50 pixels = 1 meter.
PIXEL_TO_METERS = 0.02 

# Define the curb boundary (Y-coordinate in the image).
# This represents the edge of the sidewalk; adjust based on your specific video feed.
CURB_LINE_Y = 500 

# Logging configuration for standard output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def calculate_real_distance(p1: tuple, p2: tuple) -> float:
    """
    Calculate the real-world distance in meters between two points in the image.
    Uses the Pythagorean theorem (hypot) scaled by the conversion factor.
    """
    pixel_dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    return round(pixel_dist * PIXEL_TO_METERS, 2)

def analyze_frame_parking(frame_detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze every vehicle in a frame relative to the curb and other nearby vehicles.
    Determines if the parking behavior is legal or efficient.
    """
    analysis_results = []
    
    for i, vehicle in enumerate(frame_detections):
        track_id = vehicle["track_id"]
        
        # Determine the vehicle's ground contact point (bottom-center of the bounding box)
        car_pos = (vehicle["center_x"], vehicle["bounding_box"][3]) 
        
        # 1. Calculate Curb Proximity (Distance to the sidewalk edge)
        # We calculate the vertical distance between the car's bottom and the curb line
        dist_to_curb = abs(car_pos[1] - CURB_LINE_Y) * PIXEL_TO_METERS
        
        # Parking Logic Decision Tree
        if car_pos[1] > CURB_LINE_Y + 20: 
            # If the bottom of the car is significantly past the curb line
            status = "Illegal: On Curb"
        elif dist_to_curb < 0.4:
            # If the car is within 40cm of the curb
            status = "Perfectly Parked"
        else:
            # If the car is too far away from the sidewalk edge
            status = "Far from Curb"

        # 2. Inter-vehicle Distance (Distance to the nearest neighboring car)
        nearest_neighbor_dist = float('inf')
        for j, other_vehicle in enumerate(frame_detections):
            if i == j: continue  # Skip comparing the car to itself
            
            other_pos = (other_vehicle["center_x"], other_vehicle["bounding_box"][3])
            d = calculate_real_distance(car_pos, other_pos)
            
            if d < nearest_neighbor_dist:
                nearest_neighbor_dist = d

        # Compile the spatial analysis for this specific vehicle
        analysis_results.append({
            "track_id": track_id,
            "distance_to_curb_m": round(dist_to_curb, 2),
            "nearest_car_m": nearest_neighbor_dist if nearest_neighbor_dist != float('inf') else 0,
            "status": status
        })
        
    return analysis_results

def run_distance_analysis():
    """
    Main controller that links vehicle tracking results with spatial calculations.
    """
    logger.info("Starting Tracking and Distance Analysis...")
    
    # Retrieve tracking data (Processing the video occurs here)
    all_detections = process_video()
    
    final_report = []
    
    for frame_idx, frame_dets in enumerate(all_detections):
        if not frame_dets: continue
        
        # Analyze parking metrics for the current frame
        frame_analysis = analyze_frame_parking(frame_dets)
        final_report.append({
            "frame_number": frame_idx + 1,
            "analysis": frame_analysis
        })

        # Progress reporting: Log a sample of results every 50 frames to ensure "clean" execution
        if (frame_idx + 1) % 50 == 0:
            logger.info(f"Analyzed {frame_idx + 1} frames...")
            for car in frame_analysis:
                print(f"  - Car {car['track_id']}: Dist to Curb: {car['distance_to_curb_m']}m | Status: {car['status']}")

    return final_report

if __name__ == "__main__":
    # Execute the analysis and prepare data for the dashboard
    report = run_distance_analysis()
    logger.info("Analysis Complete. Global-Standard Data Ready for Dashboard.")