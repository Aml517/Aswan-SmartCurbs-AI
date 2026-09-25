"""Final annotated video: occupancy + available capacity + vehicle gaps + violation count (needs run of occupancy first)."""
import cv2
import numpy as np

from common import load_json, path
from distance import describe
from occupancy import OCCUPANCY_JSON, PARKING_SPACES
from track import INPUT_VIDEO

FINAL_VIDEO_PATH = path("outputs/ASWAN_SMART_CURBS_FINAL.mp4")


def draw_dashboard(frame, capacity, violations_count):
    h, w, _ = frame.shape
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 60), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    cv2.putText(frame, "ASWAN - SMART CURBS AI", (10, 24), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
    text = f"Total: {capacity['total']} | Occupied: {capacity['occupied']} | Available: {capacity['available']} | Violation candidates: {violations_count}"
    cv2.putText(frame, text, (10, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)


def visualize_system(results_json=OCCUPANCY_JSON, output_path=FINAL_VIDEO_PATH):
    if not results_json.exists():
        print(f"Error: {results_json} not found. Run occupancy.py or run_pipeline.py first.")
        return
    results = load_json(results_json)
    distances = {d["frame_number"]: d["distances"] for d in load_json(path("outputs/distances.json"))} \
        if path("outputs/distances.json").exists() else {}
    tracks = load_json(path("outputs/tracks.json"))["frames"] if path("outputs/tracks.json").exists() else []
    n_viol = len(load_json(path("outputs/violations.json"))) if path("outputs/violations.json").exists() else 0

    cap = cv2.VideoCapture(str(INPUT_VIDEO))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), cap.get(cv2.CAP_PROP_FPS) or 25.0, (w, h))
    for i, data in enumerate(results):
        ok, frame = cap.read()
        if not ok:
            break
        draw_dashboard(frame, data["capacity"], n_viol)
        for sid, info in data["spaces"].items():
            pts = np.array(PARKING_SPACES[int(sid)], np.int32)
            busy = info["status"] == "Occupied"
            color = (0, 0, 255) if busy else (0, 255, 0)
            cv2.polylines(frame, [pts], True, color, 2)
            if busy:
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], color)
                cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
                c = np.mean(pts, axis=0).astype(int)
                plate_text = info.get('plate', 'Unknown')
                label = f"ID:{info['vehicle_id']} | Plate:{plate_text}"
                cv2.putText(frame, label, (int(c[0]) - 40, int(c[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        # nearest-neighbour gap label ("Car 3 - 82 cm - Car 5") for the closest pair in this frame
        pairs = distances.get(data["frame_number"], [])
        if pairs and i < len(tracks):
            best = min(pairs, key=lambda d: d["gap_cm"] if d["gap_cm"] is not None else d["distance_pixels"])
            cv2.putText(frame, describe(best), (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        writer.write(frame)
    cap.release(); writer.release()
    print(f"Final video saved: {output_path}")


if __name__ == "__main__":
    visualize_system()
