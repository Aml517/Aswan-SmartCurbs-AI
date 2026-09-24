import cv2
import json
import numpy as np

IMAGE_PATH = "parking_frame.jpg"
OUTPUT_FILE = "parking_spaces.json"

points = []
parking_spaces = []
space_id = 1

def mouse_callback(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append([x, y])
        print(f"Point {len(points)}: ({x}, {y})")
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        cv2.imshow("Select Parking Spaces", frame)

# =========================
# Load Image
# =========================
frame = cv2.imread(IMAGE_PATH)
if frame is None:
    print("ERROR: Could not open parking_frame.jpg")
    exit()

original = frame.copy()
cv2.namedWindow("Select Parking Spaces")
cv2.setMouseCallback("Select Parking Spaces", mouse_callback)

print("--------------------------------")
print("Parking Space Selection")
print("--------------------------------")
print("Click 4 points for each parking space.")
print("After 4 points:")
print("Press S = Save this space")
print("Press R = Reset current space")
print("Press Q = Finish")
print("--------------------------------")

while True:
    cv2.imshow("Select Parking Spaces", frame)
    key = cv2.waitKey(1) & 0xFF

    # Save current parking space
    if key == ord("s"):
        if len(points) == 4:
            parking_spaces.append({
                "id": space_id,
                "points": points.copy()
            })
            print(f"Space {space_id} saved.")
            space_id += 1
            points = []
            frame = original.copy()

            # Draw saved spaces
            for space in parking_spaces:
                pts = space["points"]
                pts_arr = np.array(pts, dtype=np.int32)
                polygon = cv2.convexHull(pts_arr)
                cv2.polylines(frame, [polygon], True, (255, 0, 0), 2)
                
                x, y = pts[0]
                cv2.putText(frame, f"Space {space['id']}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        else:
            print("You must select exactly 4 points.")

    # Reset current space
    elif key == ord("r"):
        points = []
        frame = original.copy()
        for space in parking_spaces:
            pts = space["points"]
            pts_arr = np.array(pts, dtype=np.int32)
            polygon = cv2.convexHull(pts_arr)
            cv2.polylines(frame, [polygon], True, (255, 0, 0), 2)
        print("Current points reset.")

    # Finish
    elif key == ord("q"):
        break

cv2.destroyAllWindows()

# =========================
# Save JSON
# =========================
with open(OUTPUT_FILE, "w") as f:
    json.dump(parking_spaces, f, indent=4)

print("\n================================")
print("Parking spaces saved successfully!")
print("File:", OUTPUT_FILE)
print("Number of spaces:", len(parking_spaces))
print("================================")