from ultralytics import YOLO
import math
import cv2


# Load YOLO model
model = YOLO("yolo11n.pt")

# Input video
input_video = "data/input.mp4"

# Open video
cap = cv2.VideoCapture(input_video)

if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Run detection + tracking
    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
       verbose=False,
        classes=[2, 3, 5, 7]  
    )

    result = results[0]

    # Store vehicle centers
    centers = []

    if result.boxes is not None and result.boxes.id is not None:

        boxes = result.boxes.xyxy.cpu().numpy()
        ids = result.boxes.id.cpu().numpy().astype(int)

        for box, vehicle_id in zip(boxes, ids):

            x1, y1, x2, y2 = box

            # Calculate center
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            centers.append(
                (vehicle_id, center_x, center_y)
            )

            # Draw bounding box
            cv2.rectangle(
                frame,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                (255, 0, 0),
                2
            )

            # Draw ID
            cv2.putText(
                frame,
                f"ID: {vehicle_id}",
                (int(x1), int(y1) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2
            )

            # Draw center
            cv2.circle(
                frame,
                (center_x, center_y),
                5,
                (0, 0, 255),
                -1
            )

    # Calculate distances between vehicles
    for i in range(len(centers)):

        for j in range(i + 1, len(centers)):

            id1, x1, y1 = centers[i]
            id2, x2, y2 = centers[j]

            distance = math.sqrt(
                (x2 - x1) ** 2 +
                (y2 - y1) ** 2
            )

            print(
                f"Vehicle {id1} <-> Vehicle {id2}: "
                f"{distance:.2f} pixels"
            )

            # Draw line between vehicles
            cv2.line(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Display distance
            middle_x = int((x1 + x2) / 2)
            middle_y = int((y1 + y2) / 2)

            cv2.putText(
                frame,
                f"{distance:.1f} px",
                (middle_x, middle_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

    # Show frame
    cv2.imshow(
        "Vehicle Detection + Tracking + Distance",
        frame
    )

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()