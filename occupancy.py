import cv2
import json
import numpy as np
from ultralytics import YOLO
from pathlib import Path

# =========================
# Settings
# =========================
VIDEO_PATH = Path("data/input.mp4")
OUTPUT_PATH = Path("outputs/occupancy_output.mp4")
PARKING_FILE = Path("parking_spaces.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# =========================
# Load Parking Spaces
# =========================
with open(PARKING_FILE, "r") as f:
    parking_spaces = json.load(f)

def is_inside(point, polygon):
    """Check if a vehicle center is inside a parking space."""
    return cv2.pointPolygonTest(polygon, point, False) >= 0

# =========================
# Open Video & YOLO
# =========================
model = YOLO("yolo11n.pt")
cap = cv2.VideoCapture(str(VIDEO_PATH))

if not cap.isOpened():
    print("ERROR: Could not open video.")
    exit()

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(str(OUTPUT_PATH), fourcc, fps, (width, height))

# =========================
# Process Video
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Run YOLO Tracking (Filtering classes: 2=Car, 3=Motorcycle, 5=Bus, 7=Truck)
    results = model.track(frame, persist=True, classes=[2, 3, 5, 7], verbose=False)
    
    vehicle_centers = []
    
    if results[0].boxes is not None and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        for box in boxes:
            x1, y1, x2, y2 = box
            # Calculate Center of Vehicle
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            vehicle_centers.append((cx, cy))
            # Draw Center Dot
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

    # 2. Check Parking Occupancy
    for space in parking_spaces:
        space_id = space["id"]
        pts = space["points"]
        
        # OpenCV 5.0 Fix (Numpy Array)
        pts_arr = np.array(pts, dtype=np.int32)
        polygon = cv2.convexHull(pts_arr)
        
        occupied = False
        for center in vehicle_centers:
            if is_inside(center, polygon):
                occupied = True
                break
                
        # Color & Status
        color = (0, 0, 255) if occupied else (0, 255, 0) # Red for Occupied, Green for Free
        status = "Occupied" if occupied else "Free"
        
        # Draw Space Box and Text
        cv2.polylines(frame, [polygon], True, color, 2)
        x, y = pts[0]
        cv2.putText(frame, f"Space {space_id}: {status}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow("Parking Occupancy", frame)
    out.write(frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
out.release()
cv2.destroyAllWindows()

print("\n================================")
print("Occupancy tracking finished!")
print("Output saved to:", OUTPUT_PATH)
print("================================")