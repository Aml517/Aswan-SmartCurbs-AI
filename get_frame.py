import cv2

video_path = "data/input.mp4"

cap = cv2.VideoCapture(video_path)

ret, frame = cap.read()

if ret:
    cv2.imwrite("parking_frame.jpg", frame)
    print("Frame saved successfully as parking_frame.jpg")
else:
    print("Could not read video.")

cap.release()